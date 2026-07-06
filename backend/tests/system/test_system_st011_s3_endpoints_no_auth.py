"""ST-011 — S3 V1 endpoints require JWT (DS-025 supersedes DS-005).

Original ST-011 asserted DS-005 (V1 has no auth) for the two S3 endpoints
GET /api/v1/dashboard and GET /api/v1/reports/sales. V2 T-092 gated these
behind ``Depends(get_current_user)``. This scenario now guards the inverse
invariant:
  - Without any Authorization header → 401.
  - With a bogus Bearer token that fails JWT decode → 401.
  - With a valid SUPERVISOR JWT (the ``client`` fixture default) → 200.
"""
from __future__ import annotations

from datetime import date


def test_st011_s3_endpoints_require_auth(client, unauthenticated_client, db_session):
    """ST-011: /dashboard and /reports/sales are gated by JWT (DS-025)."""
    today_iso = date.today().isoformat()

    # Assertion 1: GET /dashboard — no Authorization header → 401
    resp = unauthenticated_client.get(f"/api/v1/dashboard?as_of_date={today_iso}")
    assert resp.status_code == 401, (
        f"ST-011 FAIL: GET /dashboard without auth returned {resp.status_code} — "
        f"DS-025 says V1 requires JWT. Body: {resp.text}"
    )
    assert resp.headers.get("WWW-Authenticate") == "Bearer"

    # Assertion 2: GET /dashboard — bogus Bearer token → 401
    resp = unauthenticated_client.get(
        f"/api/v1/dashboard?as_of_date={today_iso}",
        headers={"Authorization": "Bearer fake"},
    )
    assert resp.status_code == 401, (
        f"ST-011 FAIL: GET /dashboard with bogus bearer returned {resp.status_code}. "
        f"Body: {resp.text}"
    )

    # Assertion 3: GET /reports/sales — no Authorization header → 401
    resp = unauthenticated_client.get("/api/v1/reports/sales")
    assert resp.status_code == 401, (
        f"ST-011 FAIL: GET /reports/sales without auth returned {resp.status_code}. "
        f"Body: {resp.text}"
    )
    assert resp.headers.get("WWW-Authenticate") == "Bearer"

    # Assertion 4: GET /reports/sales — bogus Bearer token → 401
    resp = unauthenticated_client.get(
        "/api/v1/reports/sales",
        headers={"Authorization": "Bearer fake"},
    )
    assert resp.status_code == 401, (
        f"ST-011 FAIL: GET /reports/sales with bogus bearer returned {resp.status_code}. "
        f"Body: {resp.text}"
    )

    # Assertion 5 (positive control): the default authenticated ``client``
    # reaches both endpoints — 200 confirms the guard is not blanket-blocking.
    resp = client.get(f"/api/v1/dashboard?as_of_date={today_iso}")
    assert resp.status_code == 200, (
        f"ST-011 FAIL: GET /dashboard with valid SUPERVISOR JWT returned "
        f"{resp.status_code}. Body: {resp.text}"
    )
    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, (
        f"ST-011 FAIL: GET /reports/sales with valid SUPERVISOR JWT returned "
        f"{resp.status_code}. Body: {resp.text}"
    )
