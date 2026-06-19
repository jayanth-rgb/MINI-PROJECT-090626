# Critique — T-014 DesignService

**Sprint:** S1 · **Iteration:** 1 · **Verdict:** CLEAN

## Files audited
- `backend/src/application/services/design_service.py` (29 lines)

## Decisions referenced (read first)
- **DS-007** layered architecture — service depends only on repository + schemas + domain
- **DS-008** soft delete only — no hard `delete()` exposed on repo
- **DS-012** generic BaseRepository → per-entity subclass

## Lens 1 — Spec
- LLD `files[11].functions` signatures match implementation exactly:
  - `list_designs(include_inactive: bool = False) -> list[DesignRead]` ✓
  - `create_design(payload: DesignCreate) -> DesignRead` ✓
  - `update_design(design_id: int, patch: DesignUpdate) -> DesignRead` (raises NotFoundError via repo.update) ✓
  - `deactivate_design(design_id: int) -> DesignRead` (raises NotFoundError via repo.soft_delete) ✓
- Plan `output_files = ["backend/src/application/services/design_service.py"]` — single file, no scope creep ✓
- Scope statement "Mirror of SupplierService for TradingDesign" — implementation is structurally identical to `supplier_service.py` ✓

## Lens 2 — Contract
- Imports `TradingDesignRepository` (T-006) ✓ — exists at `master.py:33`
- Imports `DesignCreate / DesignUpdate / DesignRead` (T-007) ✓ — all three present at `schemas/master.py:86–102`
- Exports `DesignService` — matches LLD `interfaces.exports` ✓
- Implicit T-003 dep (`NotFoundError`) propagates via repo; mirror service follows same pattern — acceptable ✓

## Lens 3 — Test
- **TC-020** (AC-013, create happy path): `create_design({size:"16X10", design_name:"16X10 Ridges"})` → `repo.create(payload.model_dump())` + commit + `DesignRead.model_validate`. Server defaults (`is_active=true`, `created_at`) populated by PG via SQLAlchemy 2.x `RETURNING`; session is `expire_on_commit=False`. Returned `DesignRead` includes `is_active: true`. ✓
- **TC-023** (AC-015, soft delete hides from active feed): `deactivate_design(3)` → `repo.soft_delete(3)` sets `is_active=False` + commit. Next `list_designs()` defaults `include_inactive=False` → repo filters `is_active.is_(True)` → design_id=3 absent; row physically preserved with `is_active=false`. ✓

## Lens 4 — Security
- No raw SQL — all access via SQLAlchemy ORM through repository (parameterized) ✓
- Pydantic `DesignCreate` enforces `size: min_length=1` and `design_name: min_length=1` (AC-013) at presentation boundary ✓
- `model_dump(exclude_none=True)` on update prevents accidental null-overwrite ✓
- DS-005 V1 no-auth limitation is ADR-tracked — not a critique-blocking finding ✓

## Lens 5 — Structural
- Reachable: `dependencies.py` (T-016) imports `DesignService`; `designs.py` router (T-021) wires `get_design_service` into 4 routes; `main.py` (T-023) mounts the router under `/api/v1` ✓
- No orphan functions, no dead imports ✓

## Verdict
**CLEAN** — no issues across all four primary lenses + structural reachability. Implementation is a faithful TradingDesign mirror of the already-merged SupplierService. Proceed to T-015 critique (already in_progress).
