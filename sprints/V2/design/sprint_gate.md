# Sprint Gate — V2

**Agent:** Critic (Opus) · **Timestamp:** 2026-07-02 (re-run: 2026-07-02) · **Verdict:** ✅ PASS

---

## Verdict: PASS — Phase 2 Unlocked

Re-run after fix: `framework: "pytest"` added to TC-171..TC-207 (37 TCs). All 5 substantive checks PASS. No blocking issues.

---

## Schema Validation

| File | Result | Issue |
|---|---|---|
| lld.json | ⚠️ WARN | sprint_id 'V2' ≠ `^S\d+$` — pre-acknowledged in `schema_note`; schema deficiency |
| schema.json | ⚠️ WARN | sprint_id 'V2' ≠ `^S\d+$` — pre-acknowledged; schema deficiency |
| test_cases.json | ✅ PASS | sprint_id WARN (acknowledged) · **framework field now present on all 47 TCs** |
| deps_manifest.json | ⚠️ WARN | sprint_id WARN (acknowledged) + schema format narrower than document (schema deficiency) |

**Previous FAIL (now resolved):** TC-171..TC-207 (37 TCs) were missing `"framework": "pytest"`. Fixed 2026-07-02. All 47 TCs now carry the field.

---

## Five Substantive Checks — All PASS ✓

### 1. `lld_files_cover_roadmap_scope` — ✅ PASS

All 4 `roadmap.deferred[]` items targeting V2 have complete file coverage:

| Deferred Item | Feature(s) | Module | LLD Files |
|---|---|---|---|
| User auth & RBAC | F-013, F-014 | M-008 | 11 files (models, repo, domain, service, schemas, 2 routers, dependencies, main, migration, seed) |
| Pricing, invoicing, payments | F-017, F-018, F-019 | M-011 | 9 files |
| Inward Report | F-015 | M-009 | 3 files |
| Report export PDF/Excel | F-016 | M-010 | 4 files (2 exporters + service + router) |

25 backend files total. LLD `scope_features: [F-013..F-019]` ↔ roadmap deferred V2 items: **exact match**.

### 2. `schema_entities_match_lld_models` — ✅ PASS

| LLD Persistence File | schema.json Entity |
|---|---|
| `db/models/auth.py` | `tbl_user_master` |
| `db/models/pricing.py` | `tbl_price_master` + `tbl_invoice_header` + `tbl_invoice_line` + `tbl_payment` |

5 new tables in LLD ↔ 5 new tables in schema.json ↔ 5 tables in migration 0004. **Perfect alignment.**

7 read-only reused tables from S1/S2 also documented in schema.json. `completeness_check.every_lld_model_in_schema = true` verified.

### 3. `test_cases_cover_all_ac` — ✅ PASS

21 ACs across F-013..F-019 + DS-020 — all covered:

| Feature | ACs | Status |
|---|---|---|
| F-013 (Login) | AC-054, AC-055, AC-056 | TC-171/172/173/174/175/185/186/190/191/192/208/209 ✓ |
| F-014 (RBAC) | AC-057, AC-058, AC-059, AC-060 | TC-193/194/210/211/212/213 ✓ |
| F-015 (Inward Report) | AC-061, AC-062, AC-063 | TC-195/196/197/214 ✓ |
| F-016 (Export) | AC-064, AC-065, AC-066 | TC-198/199/200/215/216 ✓ |
| F-017 (Price Master) | AC-067, AC-068 | TC-187/188/201 ✓ |
| F-018 (Invoice) | AC-069, AC-070, AC-071 | TC-176..184/189/202/203/204/217 ✓ |
| F-019 (Payments) | AC-072, AC-073 | TC-181/182/183/205/206 ✓ |
| DS-020 (TD-008 race) | AC-074 | TC-207 ✓ |

**47 TCs total · 0 uncovered ACs.**

### 4. `deps_manifest_complete` — ✅ PASS

| New Package | LLD File | Decision |
|---|---|---|
| `passlib[bcrypt] ≥1.7.4` | `domain/auth.py` | DS-018 |
| `python-jose[cryptography] ≥3.3.0` | `domain/auth.py` | DS-018 |
| `reportlab ≥4.0` | `infrastructure/exporters/pdf_exporter.py` | DS-021 |
| `openpyxl ≥3.1` | `infrastructure/exporters/excel_exporter.py` | DS-021 |

New env vars: `SECRET_KEY` (required) ✓, `ACCESS_TOKEN_EXPIRE_HOURS` (optional, default 8h) ✓

Migration `0004_v2_auth_pricing_tables.py` ✓ · Post-migration seed script ✓

No new Node packages in V2 backend — frontend deps deferred to V2 UI track.

### 5. `no_lld_conflicts_with_previous_sprint` — ✅ PASS

- **24 new files** (all `modification: create`) — no path overlap with S1/S2/S3 files
- **2 modified files** (`dependencies.py`, `main.py`) — correct integration points, modification isolated to adding auth infrastructure and new router mounts; individual V1 router files **not touched**
- **Migration chain:** 0004 sets `down_revision='0003_tx_ledger'` — correct (S3 had no schema migration, so 0003 is the last applied migration)
- **No circular dependencies** in LLD `dependency_graph_summary`
- `backend/src/infrastructure/exporters/` is a new directory with no prior sprint presence

---

## Warnings (Non-Blocking)

1. **Schema meta pattern `^S\d+$`** — All 4 design files and the sprint_gate output use sprint_id `'V2'` which doesn't match the V1-era pattern. All 4 files pre-acknowledge this. Action required: update all 5 schema files (`lld`, `schema`, `test_cases`, `deps_manifest`, `sprint_gate`) to accept `^(S\d+|V\d+)$`. Non-blocking.

2. **`deps_manifest.json` schema format** — Schema expects `packages[*].type: "runtime"|"dev"|"peer"` but document uses richer format (`ecosystem`, `purpose`, `install`, `used_in`, `decision_ref`). Schema also expects `migrations[]` as string array; document uses object array. Document format is correct and more useful. Schema needs updating. Non-blocking.

3. **OI-V2-005 already resolved** — `deps_manifest.json` open_items lists "TD-008 integration test TC to be authored at /ases-test-spec V2." TC-207 (concurrent first-row advisory lock test) IS present and maps to AC-074. OI-V2-005 can be closed.

---

## ⚑ Human Gate

**PASS — Phase 2 is unlocked.**

All 5 substantive checks PASS. No blocking issues. Warnings are schema meta-drift only — non-blocking.

**PO action required:** Review this gate report and approve to proceed.

**On PO approval:** `/ases-analyze V2`
