import sys

from sqlalchemy import select

from src.infrastructure.db.session import SessionLocal
from src.infrastructure.db.models.auth import UserModel
from src.domain.auth import get_password_hash


def seed_default_user() -> None:
    with SessionLocal() as session:
        existing = session.scalar(
            select(UserModel.id).where(UserModel.username == "admin").limit(1)
        )
        if existing is not None:
            print("admin already exists — skipping")
        else:
            user = UserModel(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="SUPERVISOR",
                is_active=True,
            )
            session.add(user)
            session.commit()
            print("seeded admin user")
        print("WARNING: Change admin password on first login.", file=sys.stderr)


if __name__ == "__main__":
    seed_default_user()
