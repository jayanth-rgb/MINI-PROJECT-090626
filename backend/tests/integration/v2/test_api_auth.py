"""V2 TC-208, TC-209, TC-210 — Auth router (login + me).

Login uses OAuth2PasswordRequestForm per DS-018 + DS-024 — form-encoded body.
"""
from __future__ import annotations

from tests.integration.v2._helpers import bearer, seed_user


def test_tc208_login_valid_credentials_returns_200_token_response(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "SUPERVISOR"
    assert body["access_token"] != ""


def test_tc209_login_wrong_password_returns_401(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "badpassword"},
    )
    assert resp.status_code == 401


def test_tc210_me_with_valid_bearer_returns_200_user_read(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    resp = client.get("/api/v1/auth/me", headers=bearer("admin", "SUPERVISOR"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert body["role"] == "SUPERVISOR"
    assert body["is_active"] is True
