"""M-009 Inward Report Service — F-015 dual-payload orchestration.

DS-017: both Consolidation and Transactions queries share a SINGLE filter
predicate built by _build_filters(). Divergent WHERE clauses between the two
queries are therefore impossible, guaranteeing reconciliation invariant
sum(transactions.nos) == sum(consolidation.total_nos) by construction. A
defense-in-depth assertion runs after both queries to surface any future
refactor that might break this property.

DS-013: place is read from InwardHeaderModel.place — the value snapshotted
from tbl_supplier_master at form-save time, NOT from a live JOIN on
SupplierModel.place.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from src.infrastructure.db.models.master import GradeModel, SupplierModel, TradingDesignModel
from src.infrastructure.db.models.transactions import InwardHeaderModel, InwardLineModel
from src.presentation.schemas.inward_report import (
    InwardConsolidationRow,
    InwardReportResponse,
    InwardTransactionRow,
)


class InwardReportService:
    """M-009: dual-payload inward report (Consolidation + Transactions) with shared filters (DS-017)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        supplier_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> InwardReportResponse:
        """Build the dual-payload Inward Report response.

        Steps:
          1. Build a single shared filter predicate list (DS-017).
          2. Run the Consolidation query (GROUP BY design + grade, ORDER BY design_name ASC).
          3. Run the Transactions query (per-line, ORDER BY purchase_date ASC).
          4. Assert: sum(transactions.nos) == sum(consolidation.total_nos) — defense-in-depth.
          5. Return InwardReportResponse.

        All filter parameters are optional; omitting all returns the full dataset.
        """
        filters = self._build_filters(date_from, date_to, supplier_ids, places, design_ids)

        consolidation = self._query_consolidation(filters)
        transactions = self._query_transactions(filters)

        consol_total = sum(r.total_nos for r in consolidation)
        txn_total = sum(r.nos for r in transactions)
        assert consol_total == txn_total, (
            f"Inward report reconciliation failed: consolidation sum={consol_total} "
            f"!= transactions sum={txn_total}"
        )

        return InwardReportResponse(consolidation=consolidation, transactions=transactions)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_filters(
        self,
        date_from: date | None,
        date_to: date | None,
        supplier_ids: list[int] | None,
        places: list[str] | None,
        design_ids: list[int] | None,
    ) -> list[ColumnElement[bool]]:
        """Build the WHERE predicates shared by BOTH queries (DS-017).

        An empty returned list (no filters applied) causes both queries to return
        the full dataset. This function is the single source of truth for all
        WHERE clauses — neither _query_consolidation nor _query_transactions
        may add inline filter predicates.
        """
        conds: list[ColumnElement[bool]] = []

        if date_from is not None:
            conds.append(InwardHeaderModel.purchase_date >= date_from)

        if date_to is not None:
            conds.append(InwardHeaderModel.purchase_date <= date_to)

        if supplier_ids:
            conds.append(InwardHeaderModel.supplier_id.in_(supplier_ids))

        if places:
            # DS-013: filter on the denormalized snapshot column on the header,
            # NOT on SupplierModel.place (which may have changed since the purchase).
            conds.append(InwardHeaderModel.place.in_(places))

        if design_ids:
            conds.append(InwardLineModel.design_id.in_(design_ids))

        return conds

    def _query_consolidation(
        self, filters: list[ColumnElement[bool]]
    ) -> list[InwardConsolidationRow]:
        """Consolidation query: GROUP BY (design, grade) with SUM(nos).

        Join path: tbl_inward_line
                   -> tbl_inward_header  (for date/supplier/place predicates)
                   -> tbl_trading_design_master
                   -> tbl_grade_master

        ORDER BY design_name ASC, grade_code ASC.
        """
        stmt = (
            select(
                InwardLineModel.design_id.label("design_id"),
                TradingDesignModel.design_name.label("design_name"),
                TradingDesignModel.size.label("size"),
                InwardLineModel.grade_id.label("grade_id"),
                GradeModel.grade_code.label("grade_code"),
                func.sum(InwardLineModel.nos).label("total_nos"),
            )
            .join(InwardHeaderModel, InwardHeaderModel.header_id == InwardLineModel.header_id)
            .join(TradingDesignModel, TradingDesignModel.design_id == InwardLineModel.design_id)
            .join(GradeModel, GradeModel.grade_id == InwardLineModel.grade_id)
            .where(*filters)
            .group_by(
                InwardLineModel.design_id,
                TradingDesignModel.design_name,
                TradingDesignModel.size,
                InwardLineModel.grade_id,
                GradeModel.grade_code,
            )
            .order_by(
                TradingDesignModel.design_name.asc(),
                GradeModel.grade_code.asc(),
            )
        )
        return [
            InwardConsolidationRow.model_validate(row, from_attributes=True)
            for row in self.session.execute(stmt).all()
        ]

    def _query_transactions(
        self, filters: list[ColumnElement[bool]]
    ) -> list[InwardTransactionRow]:
        """Transactions query: one row per inward_line with full context columns.

        Join path: tbl_inward_header
                   -> tbl_inward_line       (for design/grade predicates)
                   -> tbl_trading_design_master
                   -> tbl_grade_master
                   -> tbl_supplier_master   (for supplier_name display only)

        place is read from InwardHeaderModel.place — the denormalized snapshot
        per DS-013, NOT from SupplierModel.place.

        ORDER BY purchase_date ASC, header_id ASC.
        """
        stmt = (
            select(
                InwardHeaderModel.purchase_date.label("purchase_date"),
                InwardHeaderModel.supplier_id.label("supplier_id"),
                SupplierModel.supplier_name.label("supplier_name"),
                InwardHeaderModel.place.label("place"),  # DS-013 denormalized snapshot
                InwardLineModel.design_id.label("design_id"),
                TradingDesignModel.design_name.label("design_name"),
                TradingDesignModel.size.label("size"),
                InwardLineModel.grade_id.label("grade_id"),
                GradeModel.grade_code.label("grade_code"),
                InwardLineModel.nos.label("nos"),
            )
            .join(InwardLineModel, InwardLineModel.header_id == InwardHeaderModel.header_id)
            .join(TradingDesignModel, TradingDesignModel.design_id == InwardLineModel.design_id)
            .join(GradeModel, GradeModel.grade_id == InwardLineModel.grade_id)
            .join(SupplierModel, SupplierModel.supplier_id == InwardHeaderModel.supplier_id)
            .where(*filters)
            .order_by(
                InwardHeaderModel.purchase_date.asc(),
                InwardHeaderModel.header_id.asc(),
            )
        )
        return [
            InwardTransactionRow.model_validate(row, from_attributes=True)
            for row in self.session.execute(stmt).all()
        ]
