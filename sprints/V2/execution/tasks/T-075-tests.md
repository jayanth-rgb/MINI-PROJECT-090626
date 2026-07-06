# T-075 tests — none direct

`test_required=false` per LLD. Seed script verified by:

- **PO manual run** (pre-integration-test): `cd backend && python scripts/seed_default_user.py` after `alembic upgrade head`.
- **TC-208** (integration): `POST /api/v1/auth/login {username: "admin", password: "admin123"}` → HTTP 200. Implicitly confirms seed script ran and hash stored correctly.

No automated test for idempotency — manual second-run check during PO bring-up step.
