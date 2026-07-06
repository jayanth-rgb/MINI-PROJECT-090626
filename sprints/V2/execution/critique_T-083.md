# Critique — T-083 `services/pricing_service.py` — Iteration 1

**Verdict: CLEAN** · 0 critical · 0 major · 2 minor (both ADR tradeoffs)

---

## Lens 1 — Spec ✓

All three LLD function signatures match exactly:

| Method | LLD spec | Implementation |
|---|---|---|
| `list_prices()` | `→ list[PriceMasterModel]` | ✓ |
| `create_price(data: PriceMasterCreate)` | `→ PriceMasterModel` | ✓ |
| `update_price(price_id: int, data: PriceMasterUpdate)` | `→ PriceMasterModel` | ✓ |

- `list_prices` correctly delegates to `PriceMasterRepository.list_all()` ✓
- SELECT-before-INSERT uniqueness check — DoD: "not IntegrityError catch" ✓
- Partial-patch semantics via `data.model_dump(exclude_none=True)` ✓
- No `delete_price` method — DS-008 soft-delete compliance ✓
- `unit_price >= 0`: enforced by `PriceMasterCreate.unit_price = Field(ge=0)` at Pydantic schema layer. DS-007 compliant (Pydantic validates before service is reached). ✓

**Notable adaptation**: Plan pseudo-code used `HTTPException(404/409)` directly. Implementation uses `NotFoundError`/`ConflictError` — the established codebase pattern (see `design_grade_map_service.py`). Error handlers in `errors.py` convert these to correct HTTP status codes.

---

## Lens 2 — Contract

- Exports `["PricingService"]` ✓
- All expected interfaces imported and used: `PriceMasterRepository`, `PriceMasterCreate`, `PriceMasterUpdate` ✓
- DI factory `get_pricing_service(db) → PricingService(db)` (T-088) — constructor matches ✓
- Pricing router (T-090) methods match ✓

### I-001 (minor, ADR tradeoff) — DS-012 deviation: direct query in service

`self._db.scalar(select(PriceMasterModel)...)` at line 25–31 constructs a query directly in the service layer. DS-012 states "Services never construct queries directly." The canonical fix is `PriceMasterRepository.find_duplicate(design_id, grade_id, effective_from)` — but the plan.md pseudo-code explicitly specified this pattern and adding a repo method is out of T-083's `output_files[]` scope.

**is_adr_tradeoff: true** — plan explicitly specifies direct query; fix requires out-of-scope file. Accept as-is; log TD at sprint-close.

---

## Lens 3 — Test

TC-201 coverage:
- Seed existing (design=1, grade=1, eff_from=2026-07-01) → call create_price with same tuple → SELECT finds existing → `ConflictError` → HTTP 409 via handler ✓

### I-002 (minor, ADR tradeoff) — TC-201 exception type mismatch

TC-201 specifies `should_raise: "HTTPException(status_code=409)"`. Implementation raises `ConflictError`. Via TestClient (HTTP-level), `response.status_code == 409` is satisfied. Via unit test `pytest.raises(HTTPException)` — would fail.

**is_adr_tradeoff: true** — `ConflictError` is the correct codebase pattern. No fix needed in `pricing_service.py`. At `/ases-test-impl`:
- Use `TestClient` and assert `response.status_code == 409`, OR
- Catch `ConflictError` directly in unit test

---

## Lens 4 — Security ✓

- All queries via SQLAlchemy ORM (parameterized) — no SQL injection ✓
- No raw SQL ✓
- No secret exposure ✓
- TOCTOU on SELECT-before-INSERT: if concurrent duplicate slips through, `IntegrityError` → global 409 handler fires. Acceptable safety net.

---

## Positive Observations

- All LLD signatures match exactly ✓
- ConflictError/NotFoundError pattern consistent with codebase (not a plan deviation in spirit) ✓
- `self._db.commit()` after every mutation ✓
- `model_dump(exclude_none=True)` correctly implements partial PATCH semantics ✓
- No hard delete method — DS-008 compliant ✓

---

**Next**: Update tasks.json status → complete, update context.json.
