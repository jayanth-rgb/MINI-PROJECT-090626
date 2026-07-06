# T-075 — `scripts/seed_default_user.py` — default admin seeder

**Module:** M-008 · **Wave:** 2 (after T-067 + T-068) · **Depends on:** T-067 (UserModel), T-068 (get_password_hash)

## Context anchor

One-shot post-migration utility. Run once by PO after `alembic upgrade head` on a fresh DB. Mirrors the idempotent pattern of existing seed/fixture scripts. The seeded user provides the SUPERVISOR account needed for all management operations and for initial login by the admin.

## Implementation logic

```python
#!/usr/bin/env python
# backend/scripts/seed_default_user.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select
from infrastructure.db.session import get_db
from infrastructure.db.models.auth import UserModel
from domain.auth import get_password_hash

_DEFAULT_USERNAME = "admin"
_DEFAULT_PASSWORD = "admin123"
_DEFAULT_ROLE = "SUPERVISOR"


def seed_default_user() -> None:
    db = next(get_db())
    try:
        existing = db.scalar(
            select(UserModel).where(UserModel.username == _DEFAULT_USERNAME)
        )
        if existing:
            print(f"{_DEFAULT_USERNAME} already exists — skipping")
            return

        user = UserModel(
            username=_DEFAULT_USERNAME,
            password_hash=get_password_hash(_DEFAULT_PASSWORD),
            role=_DEFAULT_ROLE,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"seeded {_DEFAULT_USERNAME} user")
        print(
            "WARNING: Change admin password on first login.",
            file=sys.stderr
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed_default_user()
```

## Constraints

- Script is idempotent — second run produces no error, no duplicate row.
- WARNING printed to `stderr` (not `stdout`) so CI/CD pipelines can differentiate informational output from warnings.
- `sys.path.insert` needed because this script runs outside the normal `src/` package root.
- No `session.autocommit` — uses explicit `db.commit()` after add.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `cd backend && python scripts/seed_default_user.py` → stdout: `seeded admin user`, stderr: `WARNING: Change admin password on first login.`. Second run → stdout: `admin already exists — skipping`.
- **Automated**: TC-208 (POST /auth/login admin/admin123 → 200) verifies the seeded user is functional once the PO runs this script.
- **DoD**: Script exits 0 on first run and repeat run. Hashed password stored (not plaintext). WARNING on stderr.

## Checkout

> *"scripts/seed_default_user.py created. Idempotent SUPERVISOR seeder for admin/admin123. Prints WARNING to stderr. Ready for PO bring-up step."*
