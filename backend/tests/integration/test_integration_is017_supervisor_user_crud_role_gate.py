"""IS-017 — DF-Users: SUPERVISOR creates STAFF → STAFF blocked from write endpoint
→ SUPERVISOR promotes → new token allowed → soft-delete → login denied.

Uses the default client fixture (SUPERVISOR JWT auto-attached from conftest)
for admin steps. STAFF/promoted logins go through /api/v1/auth/login with
form-encoded body and use per-request headers= override.
"""
from __future__ import annotations

from datetime import date

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)


def _login(client, username: str, password: str) -> str:
    """Return access_token from /auth/login. Assumes success."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, f"login({username}) failed: {resp.text}"
    return resp.json()["access_token"]


def test_is017(client, db_session):
    # Seed master so /prices POST body is FK-valid (design_id=1, grade_id=1).
    db_session.add(TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges"))
    db_session.add(GradeModel(grade_id=1, grade_code="1"))
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1, is_active=True))
    db_session.flush()

    today_iso = date.today().isoformat()

    # STEP 1 — SUPERVISOR creates STAFF user
    resp_create = client.post(
        "/api/v1/users",
        json={
            "username": "jane_staff",
            "password": "staff-pass-01",
            "role": "STAFF",
        },
    )
    assert resp_create.status_code == 201, f"create user failed: {resp_create.text}"
    created = resp_create.json()
    assert created["role"] == "STAFF"
    assert created["is_active"] is True
    user_id = created["id"]

    # STEP 2 — jane_staff logs in
    staff_token = _login(client, "jane_staff", "staff-pass-01")
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # STEP 3 — STAFF hits SUPERVISOR-only POST /prices → 403
    resp_forbidden = client.post(
        "/api/v1/prices",
        json={
            "design_id": 1,
            "grade_id": 1,
            "unit_price": "99.00",
            "effective_from": today_iso,
        },
        headers=staff_headers,
    )
    assert resp_forbidden.status_code == 403, (
        f"STAFF should get 403 on /prices POST, got {resp_forbidden.status_code}: "
        f"{resp_forbidden.text}"
    )

    # STEP 4 — SUPERVISOR promotes STAFF → SUPERVISOR (default client JWT)
    resp_patch = client.patch(
        f"/api/v1/users/{user_id}",
        json={"role": "SUPERVISOR"},
    )
    assert resp_patch.status_code == 200, f"PATCH user failed: {resp_patch.text}"
    assert resp_patch.json()["role"] == "SUPERVISOR"

    # STEP 5 — fresh login → new JWT with SUPERVISOR role in claims
    promoted_token = _login(client, "jane_staff", "staff-pass-01")
    promoted_headers = {"Authorization": f"Bearer {promoted_token}"}

    # STEP 6 — same POST /prices now succeeds
    resp_allowed = client.post(
        "/api/v1/prices",
        json={
            "design_id": 1,
            "grade_id": 1,
            "unit_price": "99.00",
            "effective_from": today_iso,
        },
        headers=promoted_headers,
    )
    assert resp_allowed.status_code == 201, (
        f"promoted user should get 201 on /prices POST, got {resp_allowed.status_code}: "
        f"{resp_allowed.text}"
    )

    # STEP 7 — SUPERVISOR soft-deletes jane_staff
    resp_del = client.delete(f"/api/v1/users/{user_id}")
    assert resp_del.status_code == 204, f"DELETE user failed: {resp_del.text}"

    # STEP 8 — deactivated user cannot log in (AuthService returns 401)
    resp_login_denied = client.post(
        "/api/v1/auth/login",
        data={"username": "jane_staff", "password": "staff-pass-01"},
    )
    assert resp_login_denied.status_code == 401, (
        f"deactivated user should get 401, got {resp_login_denied.status_code}: "
        f"{resp_login_denied.text}"
    )
