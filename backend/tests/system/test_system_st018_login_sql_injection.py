"""ST-018 — SQL injection payloads in POST /auth/login return 401 (not 500, not 200).

Verifies parameterized SQL protects the login path. All canonical injection
payloads must return 401 (auth fail), never 200 (bypass) and never 500 (SQL
error leak). Also verifies tbl_user_master is unaffected by the DROP TABLE
attempt.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from src.domain.auth import get_password_hash
from src.infrastructure.db.models.auth import UserModel


INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "admin' --",
    "'; DROP TABLE tbl_user_master;--",
    "' UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
]


@pytest.mark.parametrize("username", INJECTION_PAYLOADS)
def test_st018_sql_injection_username_returns_401(
    unauthenticated_client, db_session, username
):
    # Seed a real user so a successful bypass would be observable via 200
    db_session.add(
        UserModel(
            username="real_admin",
            password_hash=get_password_hash("real-pass-18"),
            role="SUPERVISOR",
            is_active=True,
        )
    )
    db_session.flush()

    resp = unauthenticated_client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "anything"},
    )
    assert resp.status_code == 401, (
        f"expected 401 for injection payload {username!r}, got {resp.status_code}: "
        f"{resp.text[:200]}"
    )

    # tbl_user_master must still exist and contain real_admin
    count = db_session.execute(
        text("SELECT COUNT(*) FROM tbl_user_master WHERE username = 'real_admin'")
    ).scalar_one()
    assert count == 1, (
        f"tbl_user_master appears corrupted after injection payload {username!r} "
        f"(real_admin count = {count})"
    )
