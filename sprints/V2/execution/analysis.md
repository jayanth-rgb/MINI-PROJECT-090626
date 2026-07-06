# `/ases-analyze V2` — Sprint Analysis

**Verdict: READY**
**Timestamp:** 2026-07-02
**Graph-assisted:** yes (df03a51b — 1 commit stale, negligible)

---

## Scope

| | |
|---|---|
| Sprint | V2 |
| Features | F-013, F-014, F-015, F-016, F-017, F-018, F-019 |
| Modules | M-008 (Auth) · M-009 (Inward Report) · M-010 (Report Export) · M-011 (Pricing & Invoicing) |
| LLD files total | 26 (24 new · 2 modify) |
| Test cases | 47 (all framework=pytest, sprint_gate PASS) |
| New packages | 4 Python |
| New migrations | 1 (0004) |
| New env vars | 2 (SECRET_KEY, ACCESS_TOKEN_EXPIRE_HOURS) |

---

## Checks

| # | Check | Status |
|---|---|---|
| 1 | deps_manifest_packages_vs_installed | ⚠ FAIL (non-blocking) |
| 2 | deps_manifest_migrations_vs_alembic | ✓ PASS |
| 3 | lld_files_new_do_not_pre_exist | ✓ PASS |
| 4 | lld_files_modified_exist_with_expected_surface | ✓ PASS |
| 5 | lld_depends_on_resolves_to_existing_code | ✓ PASS |
| 6 | config_py_v2_settings_fields | ⚠ FAIL (non-blocking) |
| 7 | exporters_directory_exists | ⚠ FAIL (non-blocking) |
| 8 | env_vars_present_in_env_example | ⚠ PARTIAL (non-blocking) |
| 9 | no_drift_from_previous_sprints | ✓ PASS |
| 10 | carry_forward_items_acknowledged | ✓ PASS |
| 11 | graph_assisted_dependency_cross_check | ✓ PASS |

---

## Blocking Gaps

**None.** Verdict is READY.

---

## Non-Blocking Gaps (4 mandatory sprint-scaffold actions)

### DEP-V2-001 · Missing Python packages · Sprint-scaffold mandatory
4 packages in `deps_manifest.packages` not installed in `backend/.venv` and absent from `backend/requirements.txt`:

| Package | Version | Used in |
|---|---|---|
| `passlib[bcrypt]` | >=1.7.4 | domain/auth.py, scripts/seed_default_user.py |
| `python-jose[cryptography]` | >=3.3.0 | domain/auth.py |
| `reportlab` | >=4.0 | infrastructure/exporters/pdf_exporter.py |
| `openpyxl` | >=3.1 | infrastructure/exporters/excel_exporter.py |

**Resolution (sprint-scaffold):**
```bash
backend/.venv/Scripts/pip install passlib[bcrypt] python-jose[cryptography] reportlab openpyxl
# Then pin exact installed versions in backend/requirements.txt
```

---

### CFG-V2-001 · Config.py missing V2 Settings fields · Sprint-scaffold mandatory
`backend/src/config.py` `Settings` class is missing:
- `secret_key: str` — required, no default; used by `domain/auth.py → create_access_token` for HS256 signing
- `access_token_expire_hours: int = 8` — optional, defaults to 8 hours

No LLD task declares `config.py` in `output_files[]` — without explicit sprint-scaffold action, no dev task will add these fields. Auth domain code will reference missing config attributes.

**Resolution (sprint-scaffold):** Append these 2 fields to `Settings` class in `backend/src/config.py`:
```python
secret_key: str
access_token_expire_hours: int = 8
```

---

### DIR-V2-001 · Exporters directory absent · Sprint-scaffold mandatory
`backend/src/infrastructure/exporters/` does not exist. M-010 tasks target `pdf_exporter.py` and `excel_exporter.py` in this directory.

**Resolution (sprint-scaffold):** Create `backend/src/infrastructure/exporters/__init__.py` (empty).

---

### ENV-V2-001 · SECRET_KEY not in env files · Sprint-scaffold + PO action
`SECRET_KEY` absent from `.env.example`, `backend/.env.example`, and `.env`. The backend will not start once auth is wired into `main.py` after `/ases-dev`.

**Resolution:**
- **Sprint-scaffold:** Append to both `.env.example` files:
  ```
  SECRET_KEY=        # Generate with: openssl rand -hex 32 — required for JWT signing (V2)
  ACCESS_TOKEN_EXPIRE_HOURS=8   # JWT TTL in hours, default 8 (optional)
  ```
- **PO action before /ases-test-run:** Generate a real value and set `SECRET_KEY=<value>` in `.env`.

Resolves `OI-V2-001` from `deps_manifest.open_items`.

---

## Non-Blocking Notes (informational)

### NB-V2-001 · Graph 1 commit stale
Graph built at `df03a51b` (S3 base), HEAD is `79e54568` (S3 UI supplemental). Delta is frontend JS files only — no backend structural impact. Run `/ases-graphify` after sprint-scaffold to add V2 file nodes before `/ases-critique V2`.

### NB-V2-002 · Long-lived PG bring-up (CF-001 carry-forward)
V2 migration 0004 adds 5 tables. PO must run `alembic upgrade head && python scripts/seed_default_user.py` before live API smoke testing. No impact on `/ases-dev` or `/ases-test-run` (testcontainers handles it).

---

## Graph-Assisted Analysis Notes

- **dependencies.py hub check:** High-centrality node with 12 existing outbound edges. V2 adds 8 new exports (auth infra + 5 service factories); no existing edges removed — community structure preserved.
- **main.py god-node check:** 11 existing include_router mounts. V2 adds 6 new mounts plus auth Depends on all existing routers via include_router `dependencies=` parameter only; individual V1 router files untouched — LLD scope is correct and non-invasive.
- **SalesReportService composition:** Appears as shared node between M-005 (S3) and M-010 (V2) communities. V2's read-only composition (ReportExportService calls SalesReportService) is consistent with the graph's directed edge; no circular dependency created.

---

## Modify-Target Surface Summary

### `backend/src/presentation/api/dependencies.py`
- **Existing:** 12 DI factories (S1 + S2 + S3 additions)
- **V2 adds:** `oauth2_scheme`, `get_current_user`, `require_supervisor`, `get_auth_service`, `get_inward_report_service`, `get_report_export_service`, `get_pricing_service`, `get_invoice_service`
- **Change type:** Purely additive — no existing factory is replaced or renamed

### `backend/src/main.py`
- **Existing:** 11 `include_router` mounts (suppliers, staff, dealers, grades, designs, design_grade_map, inward, sales, adjustments, dashboard, sales_report)
- **V2 adds:** 6 new mounts (auth, users, inward_report, report_export, pricing, invoices) + `dependencies=[Depends(get_current_user)]` to all 15 protected routers
- **Change type:** Purely additive; V1 router files receive zero internal changes

---

## Depends-On Anchors Verified (existing code)

| File | Sprint | Status |
|---|---|---|
| `backend/src/infrastructure/db/base.py` | S1 | ✓ |
| `backend/src/infrastructure/db/repositories/base.py` | S1 | ✓ |
| `backend/src/infrastructure/db/models/master.py` | S1 | ✓ |
| `backend/src/infrastructure/db/repositories/master.py` | S1 | ✓ |
| `backend/src/infrastructure/db/session.py` | S1 | ✓ |
| `backend/src/infrastructure/db/models/transactions.py` | S2 | ✓ |
| `backend/src/infrastructure/db/repositories/transactions.py` | S2 | ✓ |
| `backend/src/application/services/sales_report_service.py` | S3 | ✓ |
| `backend/src/presentation/schemas/sales_report.py` | S3 | ✓ |

---

## Sprint-Scaffold Mandatory Checklist

Before `/ases-tasks V2` may run, `/ases-sprint-scaffold V2` **must** complete all 4 actions:

- [ ] **DEP-V2-001** — `pip install passlib[bcrypt] python-jose[cryptography] reportlab openpyxl` + pin in `requirements.txt`
- [ ] **CFG-V2-001** — Add `secret_key: str` + `access_token_expire_hours: int = 8` to `backend/src/config.py` Settings
- [ ] **DIR-V2-001** — Create `backend/src/infrastructure/exporters/__init__.py`
- [ ] **ENV-V2-001** — Append `SECRET_KEY=` + `ACCESS_TOKEN_EXPIRE_HOURS=8` stubs to `.env.example` and `backend/.env.example`

---

**Next:** `/ases-sprint-scaffold V2`
