"""ST-020 — STAFF role rejected on SUPERVISOR-only endpoints (403).

Verifies require_supervisor DI factory enforces the role gate on POST /users,
POST /prices, POST /invoices. STAFF token has valid signature and active user
— should pass get_current_user but fail require_supervisor.
"""
from __future__ import annotations

from datetime import timedelta

from src.domain.auth import create_access_token, get_password_hash
from src.infrastructure.db.models.auth import UserModel


def _seed_staff_token(db_session) -> str:
    db_session.add(
        UserModel(
            username="staff_user",
            password_hash=get_password_hash("irrelevant"),
            role="STAFF",
            is_active=True,
        )
    )
    db_session.flush()
    return create_access_token(
        data={"sub": "staff_user", "role": "STAFF"},
        expires_delta=timedelta(hours=8),
    )


def test_st020_staff_denied_on_supervisor_post_endpoints(
    unauthenticated_client, db_session
):
    token = _seed_staff_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    r_users = unauthenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "x", "password": "abcdefgh", "role": "STAFF"},
    )
    r_prices = unauthenticated_client.post(
        "/api/v1/prices",
        headers=headers,
        json={
            "design_id": 1,
            "grade_id": 1,
            "unit_price": "100.00",
            "effective_from": "2026-01-01",
        },
    )
    r_invoices = unauthenticated_client.post(
        "/api/v1/invoices",
        headers=headers,
        params={"sales_header_id": 999},
    )

    assert r_users.status_code == 403, (
        f"POST /users STAFF expected 403, got {r_users.status_code}: {r_users.text}"
    )
    assert r_prices.status_code == 403, (
        f"POST /prices STAFF expected 403, got {r_prices.status_code}: {r_prices.text}"
    )
    assert r_invoices.status_code == 403, (
        f"POST /invoices STAFF expected 403, got {r_invoices.status_code}: "
        f"{r_invoices.text}"
    )
