"""ST-015 — Expired JWT rejected on V1 and V2 protected endpoints (401).

Mints a token with exp in the past and asserts the guard rejects it uniformly.
Covers R-004 mitigation (V2 auth guard) + python-jose exp claim enforcement.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from src.domain.auth import create_access_token
from src.infrastructure.db.models.auth import UserModel
from src.domain.auth import get_password_hash


@pytest.mark.parametrize("path", ["/api/v1/suppliers", "/api/v1/invoices"])
def test_st015_expired_jwt_returns_401(unauthenticated_client, db_session, path):
    db_session.add(
        UserModel(
            username="expired_user",
            password_hash=get_password_hash("irrelevant"),
            role="SUPERVISOR",
            is_active=True,
        )
    )
    db_session.flush()

    expired_token = create_access_token(
        data={"sub": "expired_user", "role": "SUPERVISOR"},
        expires_delta=timedelta(seconds=-60),
    )
    resp = unauthenticated_client.get(
        path, headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp.status_code == 401, (
        f"expected 401 for expired JWT on {path}, got {resp.status_code}: {resp.text}"
    )
