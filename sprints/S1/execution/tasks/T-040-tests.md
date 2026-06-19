# T-040 — Tests

| TC | AC | Scenario |
|----|----|----------|
| TC-045 | AC-016 | Mock 409 on POST /design-grade-map -> destructive toast with message containing "exists" |
| TC-046 | AC-016 | Submit with neither dropdown selected -> errors on design_id AND grade_id; onSubmit NOT called |

Files:
- `frontend/src/app/admin/design-grade-map/__tests__/page.test.tsx`
- `frontend/src/components/admin/design-grade-map/__tests__/DesignGradeMapForm.test.tsx`
