# Critique — T-045 domain.stock (HIGHEST RISK in S2)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/domain/stock.py` (148 lines, 5 public + 2 private functions)

## Decisions referenced (read first)
- **DS-002** — SELECT FOR UPDATE serialization on latest ledger row ✓
- **DS-003** — materialized running_balance + bounded forward-recompute on back-date ✓
- **DS-004** — opening_balance via closing_balance(month_first − 1 day), no scheduler ✓
- **DS-007** — pure domain layer (no HTTP, no Pydantic, Session-in/row-out) ✓

## Lens 1 — Spec

### Function roster (LLD `files[4]`)
| Function | LLD Signature | Match |
|---|---|---|
| apply_inward | (session, design_id, grade_id, date, nos, source_header_id, source_line_id) → StockLedgerModel | ✓ |
| apply_sale | same shape, delta=−nos, source_type='sale' | ✓ |
| apply_adjustment | (..., difference, source_header_id, source_line_id) → StockLedgerModel | ✓ |
| closing_balance | (session, design_id, grade_id, as_of_date) → int | ✓ |
| opening_balance | (session, design_id, grade_id, month_first_day) → int | ✓ |
| _recompute_forward | (session, design_id, grade_id, from_date_inclusive) → None | ✓ |

### Semantic correctness — back-date trace
Existing rows for (D=1, G=1): A(Jun 22, ledger=10, Δ=+30, run=30), B(Jun 25, ledger=15, Δ=+20, run=50).
`apply_inward(date=Jun 20, nos=5)`:
1. `latest = B` (run=50); `prior_balance=50`; `is_back_dated = (Jun 20 < Jun 25) = True`
2. `insert` new row C: ledger=20, Jun 20, Δ=+5, **running=55 (transiently wrong — corrected next)**
3. `_recompute_forward(Jun 20)`:
   - `prior_row = latest_as_of(Jun 19) = None` → `running = 0`
   - `rows_after(Jun 20)` ASC: C(Jun 20, 20), A(Jun 22, 10), B(Jun 25, 15)
   - Replay: C→5, A→35, B→55 ✓
4. Final: [C=5, A=35, B=55]. Correct.

### Same-day insert (not back-dated)
`apply_inward(date=Jun 25, nos=5)` when latest=B(Jun 25): `is_back_dated = (Jun 25 < Jun 25) = False`. New row gets running=55 directly; no recompute. ✓ (strict `<` is correct per LLD wording "date < prior_row.txn_date").

### Empty-ledger edge
First-ever insert: `latest = None` → `prior_balance = 0`, `is_back_dated = False`, inserts running=delta directly. ✓

### V1 sale-into-negative
`apply_sale` does not block negative `running_balance` — matches LLD note ("V1 ledger faithfully records reality; no oversell AC"). Inline comment documents the decision. ✓

### Pure-function discipline (DS-007)
- No HTTP, no Pydantic, no logging, no global state, no module-level mutation
- Session-in / row-out / int-out only
- Caller controls transaction boundary (no implicit commits) — `_recompute_forward` calls `session.flush()` but not commit ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports` = 5 public function names — all 5 defined at module level ✓
Private helpers `_apply` and `_recompute_forward` use leading underscore — correctly excluded from public API ✓

### Expects
LLD `interfaces.expects` = `[StockLedgerRepository, StockLedgerModel]`
- `StockLedgerRepository` imported from `repositories/transactions.py` (T-043) ✓
- `StockLedgerModel` imported from `models/transactions.py` (T-042) ✓

### Imports vs depends_on[]
- `backend/src/infrastructure/db/repositories/transactions.py` → imported ✓
- `backend/src/infrastructure/db/models/transactions.py` → imported ✓

### Dead-code scan
- `Session` used in 7 type annotations ✓
- `date` used as type + arithmetic with `timedelta` ✓
- `timedelta` used in opening_balance + _recompute_forward ✓
- `StockLedgerModel` used in return annotations of 4 functions ✓
- `StockLedgerRepository` instantiated in 3 functions ✓
No dead imports.

### `date` param-name shadowing
LLD specifies param name `date` for apply_*. My impl uses `date: date`. The `from __future__ import annotations` directive makes type hints lazy strings, so the annotation resolves to the imported type while the runtime name binds to the parameter. The function body forwards `date` to `_apply`'s `txn_date` param — no internal use of the `date` type constructor — so the shadowing is harmless. ✓

## Lens 3 — Test

T-045 `test_case_refs = TC-079..TC-087` — all 9 traced:

| TC | Description | Path through code |
|---|---|---|
| TC-079 | closing_balance returns running_balance of latest row ≤ as_of_date | `closing_balance` → `repo.latest_as_of` → `.running_balance` ✓ |
| TC-080 | closing_balance returns 0 when no rows | `row is None` → 0 ✓ |
| TC-081 | opening_balance(m_first) = closing_balance(m_first − 1) per DS-004 | `opening_balance` → `closing_balance(... − timedelta(days=1))` ✓ |
| TC-082 | First-month opening = 0 | reuses TC-080 path ✓ |
| TC-083 | apply_inward Δ=+10, running=prior+10 | `_apply(delta=+nos, source_type='inward')` ✓ |
| TC-084 | apply_sale Δ=−nos, running=prior−nos | `_apply(delta=-nos, source_type='sale')` ✓ |
| TC-085 | apply_adjustment Δ=difference, running=prior+difference | `_apply(delta=difference, source_type='adjustment')` ✓ |
| TC-086 | back-date triggers forward-recompute | `is_back_dated` → `_recompute_forward` → replay ASC ✓ |
| TC-087 | concurrent SAVEs serialize via SELECT FOR UPDATE | `latest_for_design_grade(for_update=True)` → repo emits `.with_for_update()` ✓ |

## Lens 4 — Security

- All inputs typed (Session, int, date, str); no raw SQL anywhere — all DB access through SQLAlchemy via repositories
- `repo.insert({...})` dict literal — keys are hard-coded, values are typed function params (no user-controlled key injection)
- No secrets, no PII, no logging, no `os.environ`
- DS-002 SELECT FOR UPDATE prevents lost-update race; CHECK(nos > 0) at the DB level (T-042) provides defense-in-depth even if domain receives bad input
- Trust boundary per DS-007: services validate via Pydantic before reaching domain — domain trusts validated input

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file currently orphaned in live call graph — downstream consumers land in T-047 (inward_service), T-048 (sales_service), T-049 (adjustment_service), T-050 (design_grade_cb_service). Documented two-step dependency.
- Import edges: `domain/stock.py` → `repositories/transactions.py` (T-043) and `models/transactions.py` (T-042). Both upstream files exist. ✓
- No circular imports: `models/transactions.py` does not import from `domain/`; `repositories/transactions.py` does not import from `domain/`.
- All 5 `apply_*` and `*_balance` exports will be called from services in T-047..T-050. `_apply` is the single internal gateway — guarantees DS-002 lock is held on every write path.

Not critique-blocking.

## Transparency notes (not findings)

1. **First-row insert race (theoretical)** — `SELECT … FOR UPDATE LIMIT 1` acquires no lock when the WHERE returns zero rows. If two sessions concurrently insert the FIRST-EVER ledger row for the same (design, grade), both can succeed with `running_balance = delta` (instead of the second one getting `2 * delta`). Likelihood is vanishingly small (once per (design, grade) lifetime) and the implementation is faithful to DS-002 + LLD. PRD has no AC for this edge; TC-087's design assumes a pre-existing row. Surfaced here for PO awareness — if V2 needs to close this gap, options include: (a) lock the design or grade master row before the ledger query, (b) advisory locks per (design, grade) pair, (c) unique-constraint-on-first-row + retry. Out of S2 scope.

2. **Inserted-row running_balance is transiently wrong in back-date path** — `_apply` sets `running_balance = prior_balance + delta` based on the LATEST row's balance, which is incorrect for a back-dated insert. `_recompute_forward` rewrites it within the same session before commit. Caller controls the transaction boundary, so observers outside the session never see the transient value. Documented in code comment + design plan.

3. **Plan.md had a dead `running = 0` line** before the `prior_row` derivation. Removed for clarity; logic is unchanged (the next line reassigns from `prior_row.running_balance` or to 0).

4. **Apply functions gained explicit type annotations** beyond plan.md's untyped signatures — added to match LLD `inputs[]/outputs[]` types verbatim. No runtime impact.

## Verdict

**CLEAN** — 5 public + 2 private functions written exactly to spec. DS-002 lock-before-read enforced via single `_apply` gateway, DS-003 back-date forward-recompute correct under hand-traced scenario, DS-004 carry-forward via pure function call. 9 TCs (TC-079..TC-087) all wired correctly. Pure-domain discipline preserved.

→ Update `tasks.json` T-045 status to `complete`, advance context. Next per execution_order: T-046 (Pydantic schemas, parallel group A still open — independent of T-045) or T-047/048/049/050 (services — now unblocked by T-045 + dependent on T-046).
