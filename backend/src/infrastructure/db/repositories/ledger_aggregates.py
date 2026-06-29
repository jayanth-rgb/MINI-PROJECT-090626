"""
LedgerAggregatesRepository — read-only aggregation over tbl_stock_ledger.

DS-016: Dashboard aggregation uses a SINGLE GROUP BY query with CASE-conditional
SUMs rather than per-(design, grade) sub-queries.  The ix_stock_ledger_dgt
composite index (design_id, grade_id, txn_date DESC, ledger_id DESC) supports
the date-range scan, keeping the query O(in-window rows) regardless of total
ledger size.
"""

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.engine import Row

from src.infrastructure.db.models.transactions import StockLedgerModel
from src.infrastructure.db.repositories.base import BaseRepository


class LedgerAggregatesRepository(BaseRepository[StockLedgerModel]):
    """Read-only aggregator over tbl_stock_ledger for dashboard monthly totals (DS-016)."""

    def sum_deltas_by_source_type(
        self,
        month_start: date,
        as_of_date: date,
    ) -> list[Row]:
        """Return one Row per (design_id, grade_id) with CASE-aggregated SUMs of:

          - inward_sum:  SUM(delta)   WHERE source_type = 'inward'
          - outward_sum: SUM(-delta)  WHERE source_type = 'sale'
                         (inverted — ledger stores sales as negative deltas;
                          the dashboard column must read as a positive outgoing qty)
          - adjust_sum:  SUM(delta)   WHERE source_type = 'adjustment'

        Window: txn_date BETWEEN :month_start AND :as_of_date (inclusive on both ends).
        Index:  ix_stock_ledger_dgt(design_id, grade_id, txn_date DESC, ledger_id DESC)
                supports the (design_id, grade_id) GROUP BY prefix plus the date-range
                scan — planner uses an Index Range Scan over the in-window rows once.

        Single SQL statement — no N+1, no Python-side aggregation (DS-016).
        func.coalesce(..., 0) guards all three sums so missing pairs return 0 not NULL.
        """
        stmt = (
            select(
                StockLedgerModel.design_id.label("design_id"),
                StockLedgerModel.grade_id.label("grade_id"),
                func.coalesce(
                    func.sum(
                        case(
                            (StockLedgerModel.source_type == "inward", StockLedgerModel.delta),
                            else_=0,
                        )
                    ),
                    0,
                ).label("inward_sum"),
                func.coalesce(
                    func.sum(
                        case(
                            (StockLedgerModel.source_type == "sale", -StockLedgerModel.delta),
                            else_=0,
                        )
                    ),
                    0,
                ).label("outward_sum"),
                func.coalesce(
                    func.sum(
                        case(
                            (StockLedgerModel.source_type == "adjustment", StockLedgerModel.delta),
                            else_=0,
                        )
                    ),
                    0,
                ).label("adjust_sum"),
            )
            .where(StockLedgerModel.txn_date.between(month_start, as_of_date))
            .group_by(StockLedgerModel.design_id, StockLedgerModel.grade_id)
        )
        return list(self.session.execute(stmt).all())
