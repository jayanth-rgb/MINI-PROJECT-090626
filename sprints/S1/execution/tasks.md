# Sprint S1 — Task DAG

**Produced by:** `/ases-tasks S1`
**Task Manager:** Opus 4.7
**Companion JSON:** [tasks.json](./tasks.json)

---

## Headline

| | |
|---|---|
| Total tasks | **40** |
| Backend tasks | 25 (T-001..T-025) |
| UI tasks | 15 (T-026..T-040) → routed via `/ases-ui-design` |
| Test cases covered | 46 / 46 (100%) |
| Parallel groups | 12 |
| Critical path length | 10 steps |
| Gaps resolved by tasks | INFRA-001 (T-009), MIGRATION-001 (T-002) |

---

## Granularity choice

Per-entity Service + Router tasks are kept SEPARATE (not bundled into one mega-task) so each `/ases-critique` pass covers a small write scope, a clear AC slice, and one test-case cluster. Shared cross-entity files (`schemas/master.py`, `repositories/master.py`, `repositories/base.py`, `api/errors.py`, `api/dependencies.py`, `main.py`, `types/masters.ts`, `master-schemas.ts`) each get a dedicated task because they aggregate concerns from multiple entities — touching them mid-entity-task would violate rule 2 (write only `output_files[]`).

---

## Critical path (backend)

```
T-001 (config) → T-002 (db base+session+env.py)
              ↓
T-004 (ORM models) → T-006 (repos) → T-010 (supplier svc) → T-016 (api deps) → T-017 (supplier router) → T-023 (main)
                                                                                                              ↓
                                                                                                  T-024 (migration 0002) → T-025 (seed)
```

Frontend critical path:

```
T-026 (types) → T-028 (api wrappers)
T-030 (zod)  →
T-033 (MasterDataTable) →
T-034 (MasterFormDialog) →  T-035..T-040 (6 admin pages in parallel)
```

---

## Parallel groups (12 batches)

| # | Tasks | Notes |
|---|-------|-------|
| 1 | T-001, T-003, T-007, T-026, T-029, T-030, T-032, T-033, T-034 | Independent — config, exceptions, schemas, types, query provider, zod schemas, admin layout, table, dialog |
| 2 | T-002 | Single — DB infrastructure trio (base/session/env.py) |
| 3 | T-004, T-005, T-008, T-027 | ORM, BaseRepository, Errors, API client |
| 4 | T-006, T-009, T-028 | Master repos, test infra, API wrappers |
| 5 | T-031 | Root layout + home page |
| 6 | T-010, T-011, T-012, T-013, T-014, T-015 | All 6 services in parallel |
| 7 | T-016 | API dependencies (single — joins all 6 services) |
| 8 | T-017, T-018, T-019, T-020, T-021, T-022 | All 6 routers in parallel |
| 9 | T-023 | Main app |
| 10 | T-024 | Alembic migration 0002 (autogenerate) |
| 11 | T-025 | Seed master data |
| 12 | T-035, T-036, T-037, T-038, T-039, T-040 | All 6 admin pages in parallel |

> Per-batch `/ases-batch-exec` should fan out one worker-dev sub-agent per task in a parallel group.

---

## Task catalog

### Backend (25 tasks)

| ID | File / Files | Purpose | TC refs | depends_on |
|----|--------------|---------|---------|------------|
| T-001 | config.py | Pydantic Settings | — | — |
| T-002 | db/base.py + session.py + alembic env.py | DB infra trio | — | T-001 |
| T-003 | domain/exceptions.py | Exception hierarchy | — | — |
| T-004 | infrastructure/db/models/master.py | 6 ORM models | — | T-002 |
| T-005 | repositories/base.py | Generic BaseRepository | — | T-002, T-003 |
| T-006 | repositories/master.py | 6 per-entity repos | — | T-004, T-005 |
| T-007 | schemas/master.py | Pydantic schemas | TC-002,003,009,013,021 | — |
| T-008 | api/errors.py | Exception handlers | — | T-003 |
| T-009 | tests/conftest.py + testcontainers | Test infra (INFRA-001) | — | T-002 |
| T-010 | application/services/supplier_service.py | F-001 service | TC-001,004,005,006 | T-006, T-007, T-003 |
| T-011 | staff_service.py | F-002 | TC-008, TC-010 | T-006, T-007, T-003 |
| T-012 | dealer_service.py | F-003 | TC-012, TC-014 | T-006, T-007, T-003 |
| T-013 | grade_service.py | F-004 | TC-017, TC-019 | T-006, T-007, T-003 |
| T-014 | design_service.py | F-005 | TC-020, TC-023 | T-006, T-007, T-003 |
| T-015 | design_grade_map_service.py | F-006 | TC-024,025,027,028,029,031,032 | T-006, T-007, T-003 |
| T-016 | api/dependencies.py | Service factories | — | T-002, T-010..T-015 |
| T-017 | api/routers/suppliers.py | /api/v1/suppliers | TC-033, TC-034 | T-016 |
| T-018 | api/routers/staff.py | /api/v1/staff | — | T-016 |
| T-019 | api/routers/dealers.py | /api/v1/dealers | — | T-016 |
| T-020 | api/routers/grades.py | /api/v1/grades | TC-035 | T-016 |
| T-021 | api/routers/designs.py | /api/v1/designs + /designs/{id}/grades | TC-036, TC-037 | T-016 |
| T-022 | api/routers/design_grade_map.py | /api/v1/design-grade-map | TC-038 | T-016 |
| T-023 | main.py | App factory | — | T-001, T-008, T-017..T-022 |
| T-024 | migrations/0002_master_tables.py | Alembic autogen | TC-018, TC-026 | T-002, T-004 |
| T-025 | scripts/seed_master_data.py | Idempotent seed | TC-007,011,015,016,022,030 | T-002, T-004, T-024 |

### UI (15 tasks) → `/ases-ui-design`

| ID | File / Files | Purpose | TC refs | depends_on |
|----|--------------|---------|---------|------------|
| T-026 | types/masters.ts | TS types | — | — |
| T-027 | lib/api/client.ts | Axios + interceptor | — | — |
| T-028 | lib/api/masters.ts | CRUD wrappers + designsApi.getGrades | — | T-026, T-027 |
| T-029 | lib/query/provider.tsx | QueryProvider | — | — |
| T-030 | lib/validation/master-schemas.ts | Zod schemas | — | — |
| T-031 | app/layout.tsx + app/page.tsx | Root layout + home redirect | — | T-029 |
| T-032 | app/admin/layout.tsx | Admin shell | — | — |
| T-033 | components/admin/MasterDataTable.tsx | Generic table | — | — |
| T-034 | components/admin/MasterFormDialog.tsx | Reusable Dialog | — | — |
| T-035 | suppliers/page.tsx + SupplierForm.tsx | F-001 admin | TC-039, TC-040 | T-028, T-030, T-033, T-034 |
| T-036 | staff/page.tsx + StaffForm.tsx | F-002 admin | TC-041 | T-028, T-030, T-033, T-034 |
| T-037 | dealers/page.tsx + DealerForm.tsx | F-003 admin | TC-042 | T-028, T-030, T-033, T-034 |
| T-038 | grades/page.tsx + GradeForm.tsx | F-004 admin | TC-043 | T-028, T-030, T-033, T-034 |
| T-039 | designs/page.tsx + DesignForm.tsx | F-005 admin | TC-044 | T-028, T-030, T-033, T-034 |
| T-040 | design-grade-map/page.tsx + DesignGradeMapForm.tsx | F-006 admin | TC-045, TC-046 | T-028, T-030, T-033, T-034 |

---

## Per-task plan/test files

For each `T-NNN`, four files are produced:
- `sprints/S1/execution/tasks/T-NNN-plan.json` — machine-readable scope + output_files[]
- `sprints/S1/execution/tasks/T-NNN-plan.md` — implementation guide (pseudo-code, constraints, success criteria)
- `sprints/S1/execution/tasks/T-NNN-tests.json` — TC refs + per-task test summary
- `sprints/S1/execution/tasks/T-NNN-tests.md` — test-running guide

Both /ases-validate and /ases-dev READ these. /ases-critique reads plan.md for context.

---

## AC ↔ Task coverage

All 19 ACs from PRD have at least one implementing task PLUS at least one test task:

| AC | Implementing task(s) | Test case(s) |
|----|---------------------|--------------|
| AC-001 | T-007, T-010, T-017, T-035 | TC-001..003, TC-033, TC-039 |
| AC-002 | T-007, T-010, T-017, T-035 | TC-004..006, TC-034, TC-040 |
| AC-003 | T-025 | TC-007 |
| AC-004 | T-007, T-011, T-018, T-036 | TC-008, TC-009, TC-041 |
| AC-005 | T-011, T-018 | TC-010 |
| AC-006 | T-025 | TC-011 |
| AC-007 | T-007, T-012, T-019, T-037 | TC-012, TC-013, TC-042 |
| AC-008 | T-012, T-019 | TC-014 |
| AC-009 | T-025 | TC-015 |
| AC-010 | T-025 | TC-016 |
| AC-011 | T-007, T-013, T-020, T-024, T-038 | TC-017, TC-018, TC-035, TC-043 |
| AC-012 | T-013, T-020 | TC-019 |
| AC-013 | T-007, T-014, T-021, T-039 | TC-020, TC-021, TC-044 |
| AC-014 | T-025 | TC-022 |
| AC-015 | T-014, T-021 | TC-023 |
| AC-016 | T-007, T-015, T-022, T-024, T-040 | TC-024..028, TC-038, TC-045, TC-046 |
| AC-017 | T-015, T-022 | TC-029 |
| AC-018 | T-025 | TC-030 |
| AC-019 | T-015, T-021, T-028 | TC-031, TC-032, TC-036, TC-037 |

---

## Gaps & open items addressed by tasks

| Gap | Task | Resolution |
|-----|------|-----------|
| **INFRA-001** — test DB strategy | T-009 | testcontainers-postgres + conftest.py; appends `testcontainers[postgres]==4.9.0` to requirements-dev.txt |
| **MIGRATION-001** — alembic env.py | T-002 | env.py created together with base.py + session.py, wired to settings.database_url + Base.metadata |

Remaining open gaps (carried, owner-assigned outside `/ases-tasks`):
- **DB-001** — PO bootstrap verify before `/ases-test-run`
- **SEC-001** — TD-003 Next.js CVE revisited at `/ases-sprint-close`
- **TD-004** — jest@29 transitive vulns revisited at `/ases-sprint-close`

---

## Next step

Sprint has 15 UI tasks → branch onto the UI track first.

→ **`/ases-ui-design S1`** — Gemini designs the UI component specification for all 15 UI tasks. Output: `sprints/S1/execution/ui_spec.json` + `ui_spec.md`. Then `/ases-ui-review S1` → `/ases-ui-scaffold S1`. Backend track can run in parallel from `/ases-validate T-001 S1`.
