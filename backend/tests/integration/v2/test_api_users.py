"""V2 TC-211, TC-212 — Users router RBAC (SUPERVISOR-only)."""
from __future__ import annotations

from tests.integration.v2._helpers import bearer, seed_user


def test_tc211_list_users_with_staff_role_returns_403(client, db_session):
    seed_user(db_session, "staffuser", role="STAFF", password="pass1234")
    resp = client.get("/api/v1/users", headers=bearer("staffuser", "STAFF"))
    assert resp.status_code == 403


def test_tc212_create_user_with_supervisor_role_returns_201(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    resp = client.post(
        "/api/v1/users",
        headers=bearer("admin", "SUPERVISOR"),
        json={
            "username": "newverifier",
            "password": "securepass1",
            "role": "VERIFIER",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "newverifier"
    assert body["role"] == "VERIFIER"
    assert body["is_active"] is True
