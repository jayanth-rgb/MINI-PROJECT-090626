"""IS-013 — DF-Auth: login → /auth/me → V1 protected endpoint round-trip.

Verifies the DS-025 route-level auth guard on V1 routers is behaviourally
equivalent to mount-level: a valid Bearer token unlocks the V1 endpoint; the
absence of one produces 401 with WWW-Authenticate: Bearer.

Uses unauthenticated_client so the login POST is not shortcut by the conftest
default SUPERVISOR JWT.
"""
from __future__ import annotations

from tests.integration.v2._helpers import seed_user


def test_is013(unauthenticated_client, db_session):
    seed_user(
        db_session,
        username="integ_admin",
        role="SUPERVISOR",
        password="integ-pass-13",
    )

    # STEP 1 — login via OAuth2 password grant (DS-024 form-encoded body)
    resp_login = unauthenticated_client.post(
        "/api/v1/auth/login",
        data={"username": "integ_admin", "password": "integ-pass-13"},
    )
    assert resp_login.status_code == 200, f"login failed: {resp_login.text}"
    token_body = resp_login.json()
    assert token_body["token_type"] == "bearer"
    assert token_body["role"] == "SUPERVISOR"
    assert token_body["access_token"], "access_token empty"
    bearer_headers = {"Authorization": f"Bearer {token_body['access_token']}"}

    # STEP 2 — /auth/me returns UserRead for the token bearer
    resp_me = unauthenticated_client.get("/api/v1/auth/me", headers=bearer_headers)
    assert resp_me.status_code == 200, f"me failed: {resp_me.text}"
    me = resp_me.json()
    assert me["username"] == "integ_admin"
    assert me["role"] == "SUPERVISOR"
    assert me["is_active"] is True

    # STEP 3 — V1 endpoint reachable with valid Bearer (auth guard passes)
    resp_suppliers = unauthenticated_client.get(
        "/api/v1/suppliers", headers=bearer_headers
    )
    assert resp_suppliers.status_code == 200, (
        f"V1 suppliers unreachable with Bearer: {resp_suppliers.text}"
    )
    assert isinstance(resp_suppliers.json(), list)

    # STEP 4 — same V1 endpoint without Bearer returns 401 (DS-025 guard)
    resp_no_auth = unauthenticated_client.get("/api/v1/suppliers")
    assert resp_no_auth.status_code == 401, (
        f"V1 suppliers should require auth: {resp_no_auth.text}"
    )
    assert resp_no_auth.headers.get("www-authenticate", "").lower().startswith(
        "bearer"
    ), (
        "expected WWW-Authenticate: Bearer header on 401 per RFC 6750 §3"
    )
