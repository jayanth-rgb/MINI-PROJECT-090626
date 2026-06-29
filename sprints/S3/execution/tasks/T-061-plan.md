# T-061 — `application/services/dashboard_service.py` — F-010 orchestration

**Module:** M-004 · **Depends on:** T-057, T-059, T-060 · **DS:** DS-002, DS-003, DS-004, DS-015, DS-016

## Context anchor
Top of Group B. All inputs from Group A now exist:
- `DashboardRow` (T-057) — projection target
- `LedgerAggregatesRepository.sum_deltas_by_source_type` (T-059) — single-query aggregate
- `DesignGradeMapRepository.list_active_all` (T-060) — row-set enumeration

Reads from existing S2 `domain/stock.py::opening_balance` (line 134) + `closing_balance` (line 123) — both O(1) latest_as_of lookups against the materialized `running_balance` (DS-003/DS-004).

## Implementation logic

```python
# backend/src/application/services/dashboard_service.py
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
        month_first = as_of_date.replace(day=1)

        # (1) Row-set: all active (design, grade) pairs across all designs.
        pairs = self._map_repo.list_active_all()

        # (2) Single GROUP BY for monthly movements (DS-016).
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

            opening = opening_balance(self.session, pair.design_id, pair.grade_id, month_first)
            closing = closing_balance(self.session, pair.design_id, pair.grade_id, as_of_date)

            # FORMULA-001 invariant — surfaces ledger corruption fast.
            assert opening + mov["inward"] - mov["outward"] + mov["adjust"] == closing, (
                f"dashboard invariant broken for (design={pair.design_id}, grade={pair.grade_id}): "
                f"opening={opening} + inward={mov['inward']} - outward={mov['outward']} "
                f"+ adjust={mov['adjust']} != closing={closing}"
            )

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

        rows.sort(key=lambda r: (r.design_name, r.grade_code))
        return rows
```

## Constraints
- **No direct SQL in this file.** Composition only — service is a use-case orchestrator.
- `pair.design` and `pair.grade` are eager-loaded by T-060's `list_active_all` (lazy='joined' on the model relationships); do NOT issue follow-up lookups.
- `assert` is intentional — DS-016 + FORMULA-001 declare the invariant as a hard correctness property. A failure indicates ledger corruption, which is exactly when we want to crash loudly.
- Sort happens in Python (not SQL) because the result set is small (typically < 30 rows in V1) and the LLD pins the order in the response shape.
- Use the existing S2 `domain.stock.opening_balance` / `closing_balance` primitives directly — do not duplicate their logic.

## Do not touch
- `backend/src/domain/stock.py` (S2 — read only)
- `backend/src/infrastructure/db/repositories/master.py` (T-060 owns the modification)
- `backend/src/infrastructure/db/repositories/ledger_aggregates.py` (T-059 owns)
- `backend/src/presentation/schemas/dashboard.py` (T-057 owns)
- Any other service in `application/services/`
- Any test file

## Success criteria
- **Manual**: with 3 active pairs and seeded ledger across June 2026, `list_as_of(date(2026,6,30))` returns 3 DashboardRow sorted by (design_name, grade_code) with the formula invariant holding.
- **Automated**: TC-115 (basic), TC-116 (empty active pairs), TC-118/119/120 (column math per AC-042..044), TC-121 (no movements in window), TC-122 (perf p95 < 500ms over 10 runs), TC-127/128/129 (sort + invariant), TC-156 (carry-forward through month boundary) all pass.
- **DoD**: Single round-trip for aggregates (only one call to `sum_deltas_by_source_type`); per-pair calls to opening/closing are O(1) each; invariant assertion present; result sorted (design_name, grade_code) ASC.

## Checkout
> *"DashboardService.list_as_of implemented — composes list_active_all + sum_deltas_by_source_type + opening/closing_balance, asserts the formula invariant, returns sorted DashboardRows. Ready for router wiring in T-064."*
