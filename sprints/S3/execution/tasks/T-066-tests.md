# T-066 tests — none direct

This is a wiring task; correctness is verified transitively by every integration test that exercises the new endpoints:

| Source task | TCs | Test of |
|---|---|---|
| T-063 | TC-159, TC-160 | DI graph (requires both routers mounted) |
| T-064 | TC-117, TC-130, TC-131, TC-132 | /api/v1/dashboard |
| T-065 | TC-140, TC-147, TC-148, TC-149, TC-158 | /api/v1/reports/sales |

If T-066 forgets a mount, all 11 tests return 404 instead of the expected 200/422 — silent regression-immune.

See [test_cases.md](../../design/test_cases.md) for full inputs/expected_output.
