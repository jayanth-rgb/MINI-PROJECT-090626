# Critique — T-060 · master.py MODIFY · `DesignGradeMapRepository.list_active_all`

**Sprint:** S3 · **Module:** M-001 · **Verdict:** CLEAN

## Summary
`DesignGradeMapRepository.list_active_all` appended cleanly to the existing S1 file. The 6 existing repository classes and the 2 existing methods on `DesignGradeMapRepository` are byte-identical to S1. The new method uses the correct JOIN-on-grade pattern with BOTH `map.is_active` AND `grade.is_active` predicates and no `design_id` filter, satisfying TC-150 / TC-151 / TC-152 and the AC-012 + AC-017 cascade requirements.

## Decisions consulted
| ID | Relevance |
|---|---|
| DS-007 | Four-layer architecture — infrastructure layer; repository owns the query. PASS. |
| DS-008 | Soft-delete only — repository must NOT expose `delete()`; new method correctly returns `is_active=true` rows. PASS. |
| DS-012 | BaseRepository[TModel] + per-entity extensions — `list_active_all` is exactly the per-entity finder pattern. PASS. |

## Critical property checks

| # | Property | Result |
|---|---|---|
| 1 | Pure additive modification — existing classes/methods byte-identical | PASS |
| 2 | JOIN on `tbl_grade_master` with BOTH `map.is_active` AND `grade.is_active` | PASS (lines 66-67) |
| 3 | No `design_id` filter on new method | PASS |
| 4 | No new imports needed | PASS — `select`, `DesignGradeMapModel`, `GradeModel` already imported (lines 1-10) |

## Lens results

### Lens 1 — Spec
PASS. Signature `list_active_all(self) -> list[DesignGradeMapModel]` matches LLD `files[7].functions[0]` exactly. Body matches `T-060-plan.md` lines 22-33 verbatim.

### Lens 2 — Contract
PASS. `DesignGradeMapRepository` (existing export from LLD `interfaces.exports`) is extended with the declared new method. All imports already present from S1. `self.session` inherited from `BaseRepository.__init__(self, session)`. The model declares `lazy='joined'` for both `.design` and `.grade` (master.py lines 101-102), so T-061's projection of `design_name` / `size` / `grade_code` will not trigger N+1.

### Lens 3 — Test
PASS for all three referenced TCs:

- **TC-150 (basic listing, 4 active pairs across 3 designs)** — no design_id filter; both predicates true; INNER JOIN succeeds → 4 rows returned.
- **TC-151 (AC-017 cascade, map deactivated)** — `DesignGradeMapModel.is_active.is_(True)` excludes the `map_id=2` row.
- **TC-152 (AC-012 cascade, grade soft-deleted)** — `GradeModel.is_active.is_(True)` in the JOIN-filter excludes the row whose parent grade is inactive. (Note: this is filtered as a WHERE predicate on the JOINed grade table; INNER JOIN semantics + the `grade.is_active` predicate together guarantee exclusion.)

### Lens 4 — Security
PASS. No user input flows into the query. Pure SQLAlchemy core expression construction — parameter binding is handled by the driver. No string interpolation, no f-strings, no exposed secrets.

### Lens 5 — Structural
PASS. `graphify-out/graph.json` exists. The new method becomes reachable from the FastAPI entry point once T-061's `DashboardService.list_as_of` calls it (per LLD `files[2].interfaces.expects`). Verifying that downstream call site is the scope of the T-061 critique. No orphan imports introduced.

## Additive modification audit
Confirmed byte-identical:
- `SupplierRepository` (line 14-15, `pass` only)
- `StaffRepository` (line 18-19, `pass` only)
- `DealerRepository` (line 22-23, `pass` only)
- `GradeRepository.get_by_code` (lines 26-30)
- `TradingDesignRepository` (line 33-34, `pass` only)
- `DesignGradeMapRepository.get_by_pair` (lines 38-44)
- `DesignGradeMapRepository.list_active_by_design` (lines 46-57)

New method `DesignGradeMapRepository.list_active_all` appended at lines 59-70 as the last method of the last class — pure additive edit.

## Issues
None.

## Next
Ready for T-061 (DashboardService) to consume `DesignGradeMapRepository.list_active_all`.
