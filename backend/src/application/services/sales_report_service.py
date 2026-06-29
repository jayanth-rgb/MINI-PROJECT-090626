"""M-005 Sales Report Service — F-011 dual-payload orchestration.

DS-017: both Consolidation and Transactions queries share a SINGLE filter
predicate built by _build_filters(). Divergent WHERE clauses between the two
queries are therefore impossible, guaranteeing AC-050 reconciliation by
construction. A defense-in-depth assertion runs after both queries to surface
any future refactor that might break this property.

DS-013: place is read from SalesHeaderModel.place — the value snapshotted from
tbl_dealer_master at form-save time, NOT from a live JOIN on DealerModel.place.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from src.infrastructure.db.models.master import DealerModel, GradeModel, TradingDesignModel
from src.infrastructure.db.models.transactions import SalesHeaderModel, SalesLineModel
from src.presentation.schemas.sales_report import (
    ConsolidationRow,
    SalesReportResponse,
    TransactionRow,
)


class SalesReportService:
    """M-005: dual-payload sales report (Consolidation + Transactions) with shared filters (DS-017)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        dealer_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> SalesReportResponse:
        """Build the dual-payload Sales Report response.

        Steps:
          1. Build a single shared filter predicate list (DS-017).
          2. Run the Consolidation query (GROUP BY design + grade, RULE-019 sort).
          3. Run the Transactions query (per-line, RULE-020 sort).
          4. Assert AC-050: sum(transactions.nos) == sum(consolidation.total_nos).
          5. Return SalesReportResponse.

        All filter parameters are optional (RULE-018); omitting all returns the
        full dataset for the visible window.
        """
        filters = self._build_filters(date_from, date_to, dealer_ids, places, design_ids)

        consolidation = self._query_consolidation(filters)
        transactions = self._query_transactions(filters)

        # AC-050: defense-in-depth — shared filter builder guarantees parity by
        # construction, but assert at runtime so any future refactor cannot
        # silently break reconciliation.
        consol_total = sum(r.total_nos for r in consolidation)
        txn_total = sum(r.nos for r in transactions)
        assert consol_total == txn_total, (
            f"AC-050 reconciliation broken: consolidation sum={consol_total} "
            f"!= transactions sum={txn_total}"
        )

        return SalesReportResponse(consolidation=consolidation, transactions=transactions)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_filters(
        self,
        date_from: date | None,
        date_to: date | None,
        dealer_ids: list[int] | None,
        places: list[str] | None,
        design_ids: list[int] | None,
    ) -> list[ColumnElement[bool]]:
        """Build the WHERE predicates shared by BOTH queries (DS-017).

        All filters are optional and multi-select per RULE-018. An empty
        returned list (no filters applied) causes both queries to return the
        full dataset. This function is the single source of truth for all
        WHERE clauses — neither _query_consolidation nor _query_transactions
        may add inline filter predicates.
        """
        conds: list[ColumnElement[bool]] = []

        if date_from is not None:
            conds.append(SalesHeaderModel.sales_date >= date_from)

        if date_to is not None:
            conds.append(SalesHeaderModel.sales_date <= date_to)

        if dealer_ids:
            conds.append(SalesHeaderModel.dealer_id.in_(dealer_ids))

        if places:
            # DS-013: filter on the denormalized snapshot column on the header,
            # NOT on DealerModel.place (which may have changed since the sale).
            conds.append(SalesHeaderModel.place.in_(places))

        if design_ids:
            conds.append(SalesLineModel.design_id.in_(design_ids))

        return conds

    def _query_consolidation(
        self, filters: list[ColumnElement[bool]]
    ) -> list[ConsolidationRow]:
        """Consolidation query: GROUP BY (design, grade) with SUM(nos).

        Join path: tbl_sales_line
                   -> tbl_sales_header  (for date/dealer/place predicates)
                   -> tbl_trading_design_master
                   -> tbl_grade_master

        ORDER BY design_name ASC, grade_code ASC — RULE-019.
        """
        stmt = (
            select(
                SalesLineModel.design_id.label("design_id"),
                TradingDesignModel.design_name.label("design_name"),
                TradingDesignModel.size.label("size"),
                SalesLineModel.grade_id.label("grade_id"),
                GradeModel.grade_code.label("grade_code"),
                func.sum(SalesLineModel.nos).label("total_nos"),
            )
            .join(SalesHeaderModel, SalesHeaderModel.header_id == SalesLineModel.header_id)
            .join(TradingDesignModel, TradingDesignModel.design_id == SalesLineModel.design_id)
            .join(GradeModel, GradeModel.grade_id == SalesLineModel.grade_id)
            .where(*filters)
            .group_by(
                SalesLineModel.design_id,
                TradingDesignModel.design_name,
                TradingDesignModel.size,
                SalesLineModel.grade_id,
                GradeModel.grade_code,
            )
            .order_by(
                TradingDesignModel.design_name.asc(),  # RULE-019
                GradeModel.grade_code.asc(),           # RULE-019
            )
        )
        return [
            ConsolidationRow.model_validate(row, from_attributes=True)
            for row in self.session.execute(stmt).all()
        ]

    def _query_transactions(
        self, filters: list[ColumnElement[bool]]
    ) -> list[TransactionRow]:
        """Transactions query: one row per sales_line with full context columns.

        Join path: tbl_sales_header
                   -> tbl_sales_line      (for design/grade predicates)
                   -> tbl_trading_design_master
                   -> tbl_grade_master
                   -> tbl_dealer_master   (for dealer_name display only)

        place is read from SalesHeaderModel.place — the denormalized snapshot
        per DS-013, NOT from DealerModel.place.

        ORDER BY sales_date ASC, header_id ASC — RULE-020.
        """
        stmt = (
            select(
                SalesHeaderModel.sales_date.label("sales_date"),
                SalesHeaderModel.dealer_id.label("dealer_id"),
                DealerModel.dealer_name.label("dealer_name"),
                SalesHeaderModel.place.label("place"),  # DS-013 denormalized snapshot
                SalesLineModel.design_id.label("design_id"),
                TradingDesignModel.design_name.label("design_name"),
                TradingDesignModel.size.label("size"),
                SalesLineModel.grade_id.label("grade_id"),
                GradeModel.grade_code.label("grade_code"),
                SalesLineModel.nos.label("nos"),
            )
            .join(SalesLineModel, SalesLineModel.header_id == SalesHeaderModel.header_id)
            .join(TradingDesignModel, TradingDesignModel.design_id == SalesLineModel.design_id)
            .join(GradeModel, GradeModel.grade_id == SalesLineModel.grade_id)
            .join(DealerModel, DealerModel.dealer_id == SalesHeaderModel.dealer_id)
            .where(*filters)
            .order_by(
                SalesHeaderModel.sales_date.asc(),   # RULE-020
                SalesHeaderModel.header_id.asc(),    # RULE-020
            )
        )
        return [
            TransactionRow.model_validate(row, from_attributes=True)
            for row in self.session.execute(stmt).all()
        ]
