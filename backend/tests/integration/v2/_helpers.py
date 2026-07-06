"""V2 integration test helpers — seeded masters, users, JWT builders.

Shared fixtures so each TC file stays focused on the single behaviour it
verifies. SECRET_KEY is set at import time so create_access_token() succeeds
even when the host has no .env file.
"""
from __future__ import annotations

import os
from datetime import timedelta

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-v2-tests")

from src.domain.auth import create_access_token, get_password_hash
from src.infrastructure.db.models.auth import UserModel
from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)


def seed_user(
    session,
    username: str,
    role: str = "SUPERVISOR",
    is_active: bool = True,
    password: str = "admin123",
) -> UserModel:
    user = UserModel(
        username=username,
        password_hash=get_password_hash(password),
        role=role,
        is_active=is_active,
    )
    session.add(user)
    session.flush()
    return user


def make_token(username: str, role: str = "SUPERVISOR") -> str:
    return create_access_token(
        data={"sub": username, "role": role},
        expires_delta=timedelta(hours=8),
    )


def bearer(username: str, role: str = "SUPERVISOR") -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(username, role)}"}


def seed_masters(
    session,
    designs: list[tuple[int, str, str]] | None = None,
    grades: list[tuple[int, str]] | None = None,
) -> None:
    """Seed the (design, grade) master rows needed by V2 pricing/inward tests.

    Each design tuple is (design_id, size, design_name). grade tuple is
    (grade_id, grade_code). autoincrement is respected — supplied ids are
    honored by SQLAlchemy for these BigInteger PKs.
    """
    designs = designs or [(1, "16X10", "16X10 Ridges")]
    grades = grades or [(1, "1")]
    for did, size, name in designs:
        session.add(TradingDesignModel(design_id=did, size=size, design_name=name))
    for gid, code in grades:
        session.add(GradeModel(grade_id=gid, grade_code=code))
    session.flush()
    for did, _, _ in designs:
        for gid, _ in grades:
            session.add(DesignGradeMapModel(design_id=did, grade_id=gid))
    session.flush()


def seed_supplier(session, supplier_id: int = 1, name: str = "Manjunatha", place: str = "Mallur") -> None:
    session.add(SupplierModel(supplier_id=supplier_id, supplier_name=name, place=place))
    session.flush()


def seed_dealer(session, dealer_id: int = 1, name: str = "Raj Hardwares", place: str = "Dindivanam") -> None:
    session.add(DealerModel(dealer_id=dealer_id, dealer_name=name, place=place))
    session.flush()


def seed_staff(session, staff_id: int = 1, name: str = "Chandran") -> None:
    session.add(StaffModel(staff_id=staff_id, staff_name=name))
    session.flush()
