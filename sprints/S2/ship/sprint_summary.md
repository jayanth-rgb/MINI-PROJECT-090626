# Sprint S2 — Close Summary

**Closed:** 2026-06-23 · **Verdict:** ready to ship · **Phase transition:** SPRINT_EXECUTION → SPRINT_SHIP

## Goal recap
Inward / Sales / Adjustment transaction forms backed by a materialized `tbl_stock_ledger` with DS-002 SELECT FOR UPDATE serialization and DS-003 / DS-004 stock arithmetic.

## Task accounting

| Status | Count | Details |
|---|---|---|
| Completed | 16 | T-041..T-056, **all CLEAN on iteration 1** |
| Deferred | 0 | — |
| Escalated | 0 | — |
| In progress | 0 | — (sprint-close pre-check satisfied per ASES rule 13) |

UI track delivered separately (no entries in `tasks.json` per LLD `frontend_ui_track_note`):
- `/ases-ui-design S2` → 13 components specified
- `/ases-ui-review S2` → APPROVED with 2 warnings (UR-W007/W008 both resolved at scaffold)
- `/ases-ui-scaffold S2` → 16 files created, 2 modified, 6 integration_points declared, **LOCKED**

## Features shipped (3)

| Feature | ACs | Backend tasks | UI |
|---|---|---|---|
| **F-007 Inward** | AC-020..027 (8) | T-042/043/045/047/051/052 | InwardForm |
| **F-008 Sales** | AC-028..033 (6) | T-042/043/045/048/051/053 | SalesForm |
| **F-009 Adjustment** | AC-034..040 (7) | T-042/043/045/049/050/051/054/055 | AdjustmentForm + AdjustmentLineRow + Err012Banner |

**Total: 21 ACs covered.**

## New architectural decisions (2)

Both already live in `.ases/decisions.json` (written by `/ases-lld S2`):

- **DS-013** — Denormalize `place` onto `tbl_inward_header` + `tbl_sales_header` (snapshot at save). Eliminates 1 JOIN on S3's Sales Report hot path; preserves historical immutability when master place is later edited.
- **DS-014** — Upgrade `TimestampMixin` to emit `DateTime(timezone=True)` and ALTER 4 S1 `created_at` columns to TIMESTAMPTZ in migration 0003. **Closes TD-007.**

## Tech debt

### Closed (1)
- **TD-007** — TimestampMixin TIMESTAMP vs LLD-prose TIMESTAMPTZ drift. Closed by DS-014 / T-041 / T-044.

### New (2)
- **TD-008 (minor, V2)** — First-row insert race: `SELECT FOR UPDATE LIMIT 1` acquires no lock when WHERE matches 0 rows. Two concurrent sessions inserting the FIRST-EVER ledger row for the same (design, grade) can each succeed at `running_balance = delta` instead of [delta, 2·delta]. Likelihood: once per (design, grade) lifetime. PRD silent; TC-087 assumes pre-existing row. Surfaced in T-045 critique (transparency note 1). V2 options: lock master row, advisory locks, unique+retry.
- **TD-009 (minor, in-sprint)** — 6 zod-only edge-case TCs (TC-090/091/094/096/098/100) deferred from `/ases-ui-scaffold` to `/ases-test-impl S2`. Routine assertions that follow a consistent pattern; deferring kept scaffold tight.

## Carry forward (1)

- **CF-001** — W5: PO bring-up of PostgreSQL container + `alembic upgrade head` + seed run. **Still pending from S1.** Phase 3 verification uses ephemeral testcontainers per IS-002 pattern, so this does not block sprint-close or ship. PO action item before any S3 work that needs persistent local PG.

## TCs to verify in Phase 3 — 56 total

### Backend (43, pytest) — TC-047..TC-089
- **F-007 Inward:** TC-047, 049, 050, 051, 054, 055, 056 (service); TC-053 (DB CHECK)
- **F-008 Sales:** TC-058..063, 065, 066 (service); TC-064 (DB CHECK)
- **F-009 Adjustment:** TC-074, 075, 077 (service); TC-067, 068, 069 (Pydantic + DB CHECK)
- **Schemas (T-046):** TC-052, 061, 067, 068, 072, 073
- **DesignGradeCb (T-050/055):** TC-070, 071
- **Domain stock (T-045 — HIGHEST RISK):** TC-079..087 (9 — incl TC-087 concurrency 2-session test)
- **Routers (T-052..055):** TC-048, 057, 066, 076, 078
- **Migration constraints (T-044):** TC-088, 089

### Frontend (13, jest) — TC-090..TC-102
- ✅ **Implemented at scaffold (7):** TC-092, 093, 095, 097, 099, 101, 102
- 🟡 **Deferred to `/ases-test-impl S2` (6):** TC-090, 091, 094, 096, 098, 100 (pure zod-validator cases)

## Phase 3 inputs

### Next sprint hints (for /ases-prd-update S3)
- **S3 scope (roadmap):** F-010 Stock Dashboard, F-011 Sales Report, F-012 Consolidation Report
- **Reuses from S2:** stock_ledger composite index (`ix_stock_ledger_dgt`), DS-004 on-read carry-forward pattern, T-048 `list_sales` 4-filter backbone, DS-013 denormalized place (no JOIN to dealer at read time)

### Suggested PRD updates for S3
1. **AC-045 dashboard latency** — re-state numerically (`p95 < 500ms`) so `/ases-system-test S3` can assert
2. **TD-008 first-row race** — PRD decision: close as "V1 acceptable" or specify mitigation

## Phase transition

```
SPRINT_EXECUTION ──/ases-sprint-close S2──► SPRINT_SHIP
                                              │
                                              ▼
                                  /ases-test-impl S2
                                              │
                                              ▼
                                  /ases-test-run S2
                                              │
                                              ▼
                                /ases-integration-test S2
                                              │
                                              ▼
                                  /ases-system-test S2
                                              │
                                              ▼
                                ⚑ /ases-uat S2 (PO gate)
                                              │
                                              ▼
                                  /ases-devops S2 (commit)
                                              │
                                              ▼
                                ⚑ /ases-final-audit S2 (PO gate)
                                              │
                                              ▼
                                    /ases-release S2 → S3
```

→ Next: `/ases-test-impl S2`
