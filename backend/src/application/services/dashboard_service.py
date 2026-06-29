"""
DashboardService — M-004 use-case orchestrator for the Stock Dashboard (F-010).

Design references:
  DS-003 / DS-004 — running_balance is materialised; opening/closing are O(1)
                    latest_as_of lookups (no live SUM needed per pair).
  DS-016          — SINGLE GROUP BY query for the monthly movement aggregates;
                    no per-(design, grade) sub-queries.
  FORMULA-001     — opening + inward − outward + adjust == closing invariant.

Performance target: p95 < 500 ms (AC-045 / DS-015).
"""

from datetime import date

from sqlalchemy.orm import Session

from src.domain.stock import closing_balance, opening_balance
from src.infrastructure.db.repositories.ledger_aggregates import LedgerAggregatesRepository
from src.infrastructure.db.repositories.master import DesignGradeMapRepository
from src.presentation.schemas.dashboard import DashboardRow


class DashboardService:
    """M-004: aggregates per-(design, grade) stock columns as of a given date.

    Plan: 1 ORM SELECT for active pairs (T-060) + 1 GROUP BY for movement SUMs (T-059)
    + 2 O(1) latest_as_of lookups per pair for opening/closing (DS-003/004). Target
    p95 < 500ms per FORMULA-001 + DS-015.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._map_repo = DesignGradeMapRepository(session)
        self._aggregates_repo = LedgerAggregatesRepository(session)

    def list_as_of(self, as_of_date: date) -> list[DashboardRow]:
        """Return one DashboardRow per active (design, grade) pair as of *as_of_date*.

        Steps:
          1. Derive the first day of the month containing *as_of_date*.
          2. Fetch all active (design × grade) pairs via DesignGradeMapRepository.list_active_all.
          3. Issue a single GROUP BY query for monthly Inward/Outward/Adjust totals.
          4. For each pair: look up opening (day before month start) and closing (as_of_date).
          5. Assert the FORMULA-001 invariant — a failure indicates ledger corruption.
          6. Return rows sorted by (design_name ASC, grade_code ASC).

        Raises AssertionError if the FORMULA-001 invariant fails for any row.
        """
        month_first = as_of_date.replace(day=1)

        # (1) Row-set: all active (design, grade) pairs across all designs (T-060).
        pairs = self._map_repo.list_active_all()

        # (2) Single GROUP BY for monthly movements — DS-016.
        #     One DB round-trip regardless of how many active pairs exist.
        agg_rows = self._aggregates_repo.sum_deltas_by_source_type(month_first, as_of_date)
        agg_by_key: dict[tuple[int, int], dict[str, int]] = {
            (r.design_id, r.grade_id): {
                "inward":  int(r.inward_sum),
                "outward": int(r.outward_sum),
                "adjust":  int(r.adjust_sum),
            }
            for r in agg_rows
        }

        rows: list[DashboardRow] = []
        for pair in pairs:
            key = (pair.design_id, pair.grade_id)
            mov = agg_by_key.get(key, {"inward": 0, "outward": 0, "adjust": 0})

            # O(1) latest_as_of lookups per DS-003/DS-004.
            # opening_balance(month_first) == closing_balance(month_first - 1 day).
            opening = opening_balance(self.session, pair.design_id, pair.grade_id, month_first)
            closing = closing_balance(self.session, pair.design_id, pair.grade_id, as_of_date)

            # FORMULA-001 invariant — surfaces ledger corruption immediately.
            # DS-016 asserts this relationship holds across all movement columns.
            assert opening + mov["inward"] - mov["outward"] + mov["adjust"] == closing, (
                f"dashboard invariant broken for (design={pair.design_id}, grade={pair.grade_id}): "
                f"opening={opening} + inward={mov['inward']} - outward={mov['outward']} "
                f"+ adjust={mov['adjust']} != closing={closing}"
            )

            # pair.design and pair.grade are eager-loaded (lazy='joined') by list_active_all —
            # accessing pair.design.design_name / pair.grade.grade_code does NOT issue extra queries.
            rows.append(
                DashboardRow(
                    design_id=pair.design_id,
                    design_name=pair.design.design_name,
                    size=pair.design.size,
                    grade_id=pair.grade_id,
                    grade_code=pair.grade.grade_code,
                    opening=opening,
                    inward=mov["inward"],
                    outward=mov["outward"],
                    adjust=mov["adjust"],
                    closing=closing,
                )
            )

        # Sort in Python — result set is small (typically < 30 rows in V1) and the
        # LLD pins the order in the response shape, not in SQL.
        rows.sort(key=lambda r: (r.design_name, r.grade_code))
        return rows
