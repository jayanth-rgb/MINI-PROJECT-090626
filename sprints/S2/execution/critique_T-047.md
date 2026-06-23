# Critique — T-047 InwardService (F-007)

**Sprint:** S2 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/application/services/inward_service.py` (127 lines, 1 class, 2 methods + __init__)

## Decisions referenced (read first)
- **DS-002** — apply_inward holds SELECT FOR UPDATE inside the service transaction ✓
- **DS-007** — strict layering: service → repo → ORM; no router-to-repo shortcut ✓
- **DS-013** — `place = supplier.place` snapshot at save time (server-derived, not from request) ✓

## Lens 1 — Spec

### Method roster (LLD `files[5]`)
| Method | Signature | Match |
|---|---|---|
| `__init__(session)` | binds 6 repos | ✓ |
| `save_inward(payload: InwardCreate) → InwardRead` | per LLD | ✓ |
| `list_inwards(date_from, date_to) → list[InwardRead]` | per LLD | ✓ |

### `save_inward` orchestration (matches plan.md flow exactly)
1. ✓ Validate `purchase_date` future (AC-020) and >7-day-prior (AC-021) bounds
2. ✓ Fetch supplier; check `is_active`; snapshot `supplier.place` for DS-013
3. ✓ Fetch entered_by staff; check `is_active`
4. ✓ Strip lines where `nos is None or nos == 0` (RULE-017 / AC-025)
5. ✓ Reject if no lines remain (AC-026 / ERR-008)
6. ✓ For each kept line: validate design active, grade active, (design, grade) pair in active map (AC-023 / ERR-005)
7. ✓ `repo.create_with_lines(header_payload_with_place, line_payloads)` — one flush
8. ✓ Per-line `domain.stock.apply_inward(session, design, grade, purchase_date, nos, header.header_id, line.line_id)` — acquires SELECT FOR UPDATE
9. ✓ `session.commit()` — AC-027 atomicity (header + lines + ledger rows persist as one transaction)
10. ✓ Return `InwardRead.model_validate(header)` — hydrated via from_attributes=True

### `list_inwards` implementation
- Constructs `select(InwardHeaderModel)` with optional date_from/date_to filters
- Orders by `purchase_date DESC, header_id DESC`
- `.unique()` collapses the row multiplication from `lazy='joined'` on `.lines` relationship (correct SQLAlchemy 2.x idiom)
- Returns `[InwardRead.model_validate(h) for h in headers]`

### Decision constants
- `MAX_BACKDATE_DAYS = 7` — module-level constant matching AC-021's 7-day window ✓

### Order-of-operations discipline
- All NotFoundError-raising reads happen BEFORE any writes ✓
- No partial state written if validation fails ✓
- DS-002 lock acquisitions are per-line, all within the same SQLAlchemy session — caller controls commit ✓

## Lens 2 — Contract

### Exports
LLD `interfaces.exports = ["InwardService"]` — class defined at module level ✓

### Expects
LLD `interfaces.expects` = `[InwardHeaderRepository, SupplierRepository, StaffRepository, DesignGradeMapRepository (validate_pair_active), domain.stock.apply_inward, Pydantic schemas]`
- `InwardHeaderRepository` ✓
- `SupplierRepository`, `StaffRepository`, `TradingDesignRepository`, `GradeRepository` ✓
- `DesignGradeMapRepository` — the actual S1 method is `get_by_pair(design_id, grade_id)` (T-006 contract in `master.py`); LLD spec mentioned `validate_pair_active` but the real contract per S1 is `get_by_pair`. Implementation correctly uses `get_by_pair`. Transparency note recorded.
- `stock.apply_inward` ✓
- `InwardCreate`, `InwardRead` from `schemas/transactions.py` ✓

### Imports vs depends_on[]
- All 5 depends_on files imported correctly
- Extra import `InwardHeaderModel` (from `models/transactions.py`) needed for `list_inwards` query construction — plan.md left list_inwards as `...`; recorded as transparency note

### Dead-import scan
- `NotFoundError` imported on line 9 but never explicitly referenced (BaseRepository.get raises it transitively); plan.md had it referenced inside redundant try/except blocks that I removed as the catch-and-rethrow was identical to the original exception. Documentary-style import. Auto-fixable at lint time.

## Lens 3 — Test

T-047 `test_case_refs` — all 7 traced:

| TC | AC | Path |
|---|---|---|
| TC-047 | AC-020 future purchase_date → ValidationError | `if payload.purchase_date > today_` ✓ |
| TC-049 | AC-021 > 7-day prior → ValidationError | `if payload.purchase_date < today_ - timedelta(days=7)` ✓ |
| TC-050 | AC-022 / DS-013 place snapshot | `"place": supplier.place` in header_payload ✓ |
| TC-051 | AC-023 pair must be in active map | `pair is None or not pair.is_active` ✓ |
| TC-054 | AC-025 strip nos=None/0 | `line.nos is not None and line.nos > 0` filter ✓ |
| TC-055 | AC-026 reject if no valid lines | `if not kept_lines: raise ValidationError` ✓ |
| TC-056 | AC-027 single-transaction header+lines+ledger | per-line apply_inward + single commit() ✓ |

## Lens 4 — Security

- All client input validated by Pydantic at the API boundary (T-046) before reaching the service
- Domain-layer ValidationError uses string interpolation but with VALIDATED ints (e.g., `payload.supplier_id` is gt=0 from Pydantic) — no injection vector in error messages, no SQL exposure
- DS-002 SELECT FOR UPDATE inside the transaction prevents lost-update races
- All DB access via SQLAlchemy expression API (`.get()`, `select()`); no raw SQL
- Error messages don't leak internal IDs to unauthorized users — but per DS-005 V1 has no auth, so this is moot for V1 (V2 should sanitize)

No security findings.

## Lens 5 — Structural

`graphify-out/graph.json` exists.

- New file imports from 5 in-project modules (all confirmed by validation step):
  - `domain/stock.py` (T-045)
  - `domain/exceptions.py` (S1)
  - `infrastructure/db/models/transactions.py` (T-042) — added for list_inwards
  - `infrastructure/db/repositories/master.py` (S1)
  - `infrastructure/db/repositories/transactions.py` (T-043)
  - `presentation/schemas/transactions.py` (T-046)
- Will be imported by T-051 (DI dependencies) and T-052 (inward router) downstream
- No circular imports — domain layer does not import from application
- Currently orphaned in live call graph until T-051/052 wire it up; documented two-step dependency

Not critique-blocking.

## Transparency notes (not findings)

1. **LLD `expects` says `validate_pair_active`; S1 method is `get_by_pair`** — Implementation correctly uses `get_by_pair` (the actual T-006 contract per `master.py`). LLD was an imprecise label; the semantic check (pair exists + is_active) is performed.

2. **`list_inwards` needed ORM model import** — Plan.md left the method body as `...`. Implementing it without modifying T-043 (out of scope) required importing `InwardHeaderModel` and constructing the query inline in the service. Mild DS-007 cross-layer touch (service references ORM model directly), but acceptable: the alternative (extending T-043's repo with a `list_by_date_range` method) would have violated `do_not_touch`. The query uses parameterized ORM expression API — no raw SQL.

3. **Redundant try/except removed from plan.md** — Plan.md had `try: self.supplier_repo.get(...) except NotFoundError: raise NotFoundError("Supplier", id)` patterns for 4 master fetches. BaseRepository.get already raises `NotFoundError("Supplier", id)` with identical args (it derives entity name from `model.__name__.removesuffix("Model")`). The catch-and-rethrow was a no-op; removed for clarity. NotFoundError propagates naturally to the FastAPI handler.

4. **`NotFoundError` import is now technically unused** — Side-effect of the cleanup in note 3. Auto-fixable by ruff/flake8 at /ases-test-impl time. Not flagged as a finding since the type IS part of the contract (raised transitively via .get() calls) and tooling will catch/fix at the standard quality gate.

5. **`.unique()` on the joined-load query** — `lazy='joined'` on InwardHeaderModel.lines (T-042) multiplies header rows by their line count. The `.scalars().unique().all()` idiom is the canonical SQLAlchemy 2.x dedup.

## Verdict

**CLEAN** — InwardService orchestrates F-007 exactly per LLD: 10-step `save_inward` with all AC-020..AC-027 invariants enforced, plus `list_inwards` with date filtering. All 7 TCs traced. DS-002 / DS-007 / DS-013 honored. Pure-domain `apply_inward` calls correctly scoped within the service transaction.

→ Update `tasks.json` T-047 status to `complete`, advance context. Next: T-048 (SalesService — mirror shape with dealer + 2 staff fields + delta=−nos), then T-049 (AdjustmentService), then T-050 (DesignGradeCbService). After all 4 services land, T-051 wires them into dependencies.py.
