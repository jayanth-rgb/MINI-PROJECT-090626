"""ST-019 — Deactivated user's still-valid token returns 401 (DS-018).

Seeds an active SUPERVISOR, mints a valid non-expired token, then flips
is_active to False and commits. Any subsequent authenticated call must return
401 because get_current_user re-reads is_active from the DB on every request.
Bounds the exposure window on deactivation to the currently-in-flight request.
"""
from __future__ import annotations

from datetime import timedelta

from src.domain.auth import create_access_token, get_password_hash
from src.infrastructure.db.models.auth import UserModel


def test_st019_deactivated_user_token_returns_401(unauthenticated_client, db_session):
    user = UserModel(
        username="soon_deactivated",
        password_hash=get_password_hash("irrelevant"),
        role="SUPERVISOR",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    valid_token = create_access_token(
        data={"sub": "soon_deactivated", "role": "SUPERVISOR"},
        expires_delta=timedelta(hours=8),
    )

    # First call while active — should pass to prove the token itself is well-formed
    ok = unauthenticated_client.get(
        "/api/v1/suppliers", headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert ok.status_code == 200, f"pre-deactivation call failed: {ok.text}"

    # Deactivate mid-life
    user.is_active = False
    db_session.flush()

    denied = unauthenticated_client.get(
        "/api/v1/suppliers", headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert denied.status_code == 401, (
        f"deactivated user was NOT rejected: {denied.status_code} {denied.text}"
    )
