# Sprint S1 — UAT Report

**Reviewed by:** Jayanth (PO) · **Date:** 2026-06-20 · **Verdict:** **APPROVED**

## Headline
**All 19 ACs (AC-001..AC-019) accepted.** 0 conditional, 0 rejected.

The PO accepted every AC as-is based on the passing automated test evidence on file (46 PRD-derived test cases + 4 cross-module integration scenarios + 3 system-test scenarios, all green). The 3 cross-feature manual checks that depend on S2/S3 transaction forms (AC-005 Inward Form dropdown, AC-008 Sales Form / report filter, AC-015 Inward/Sales/Adjustment form dropdowns) are recognized as implicit follow-ups for S2/S3 UAT — not as S1 gaps, since the underlying S1 invariants (soft-delete hides from default list, FK references preserved) are fully verified.

## Items

| Feature | AC | Verdict |
|---------|-----|---------|
| F-001 Supplier | AC-001, AC-002, AC-003 | ✓ accepted |
| F-002 Staff | AC-004, AC-005, AC-006 | ✓ accepted |
| F-003 Dealer | AC-007, AC-008, AC-009 | ✓ accepted |
| F-004 Grade | AC-010, AC-011, AC-012 | ✓ accepted |
| F-005 Design | AC-013, AC-014, AC-015 | ✓ accepted |
| F-006 Design-Grade Map | AC-016, AC-017, AC-018, AC-019 | ✓ accepted |

## Evidence sources

- Test runs: [test_run_report.md](test_run_report.md) — 46/46 TCs pass (50 test runs incl. parametrized)
- Integration: [integration_scenarios.json](integration_scenarios.json) — 4/4 IS scenarios pass
- System: [system_test_report.md](system_test_report.md) — 3/3 executed STs pass; 2 STs deferred to S3 with explicit reasons

## Pending PO action (separate from UAT verdict)

**W5** still open: bringing up the long-lived PostgreSQL via `.env` + docker-compose + `alembic upgrade head` for local manual UI walk-through. IS-002 closed the artifact-correctness portion (alembic + seed proven against an ephemeral PG container). The PO can complete W5 at their convenience — it does NOT block `/ases-devops S1` since the git commit step is environment-agnostic.

## Next step
→ `/ases-devops S1` (now unlocked — UAT gate APPROVED triggers commit-on-approval per ases-hook.py guard).
