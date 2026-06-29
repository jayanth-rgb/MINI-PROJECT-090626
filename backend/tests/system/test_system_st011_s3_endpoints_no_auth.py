"""ST-011 — V1 no-auth posture for S3 endpoints (HLD R-004, DS-005).

Mirrors S1 ST-002 which already verified S1+S2 endpoints. This scenario
verifies the two NEW S3 endpoints:
  - GET /api/v1/dashboard
  - GET /api/v1/reports/sales

Both must accept requests WITHOUT an Authorization header AND must not
reject requests that include a bogus "Authorization: Bearer fake" header
(FastAPI V1 has no auth middleware; unconfigured auth headers are ignored).

All 4 assertions must return HTTP 200.
"""
from __future__ import annotations

from datetime import date


def test_st011(client, db_session):
    """ST-011: Dashboard and Sales Report return 200 with no auth and with bogus auth header."""
    today_iso = date.today().isoformat()

    # ------------------------------------------------------------------
    # Assertion 1: GET /dashboard — no Authorization header
    # ------------------------------------------------------------------
    resp = client.get(f"/api/v1/dashboard?as_of_date={today_iso}")
    assert resp.status_code == 200, (
        f"ST-011 FAIL: GET /dashboard without auth returned {resp.status_code} — "
        f"DS-005 says V1 has no auth. Body: {resp.text}"
    )
    assert resp.status_code != 401, "Unexpected 401 on /dashboard without auth header"
    assert resp.status_code != 403, "Unexpected 403 on /dashboard without auth header"

    # ------------------------------------------------------------------
    # Assertion 2: GET /dashboard — bogus Authorization header
    # ------------------------------------------------------------------
    resp = client.get(
        f"/api/v1/dashboard?as_of_date={today_iso}",
        headers={"Authorization": "Bearer fake"},
    )
    assert resp.status_code == 200, (
        f"ST-011 FAIL: GET /dashboard with bogus auth header returned {resp.status_code} — "
        f"FastAPI should ignore unconfigured auth. Body: {resp.text}"
    )
    assert resp.status_code != 401, "Bogus Bearer token caused 401 on /dashboard"
    assert resp.status_code != 403, "Bogus Bearer token caused 403 on /dashboard"

    # ------------------------------------------------------------------
    # Assertion 3: GET /reports/sales — no Authorization header
    # ------------------------------------------------------------------
    resp = client.get("/api/v1/reports/sales")
    assert resp.status_code == 200, (
        f"ST-011 FAIL: GET /reports/sales without auth returned {resp.status_code} — "
        f"DS-005 says V1 has no auth. Body: {resp.text}"
    )
    assert resp.status_code != 401, "Unexpected 401 on /reports/sales without auth header"
    assert resp.status_code != 403, "Unexpected 403 on /reports/sales without auth header"

    # ------------------------------------------------------------------
    # Assertion 4: GET /reports/sales — bogus Authorization header
    # ------------------------------------------------------------------
    resp = client.get(
        "/api/v1/reports/sales",
        headers={"Authorization": "Bearer fake"},
    )
    assert resp.status_code == 200, (
        f"ST-011 FAIL: GET /reports/sales with bogus auth header returned {resp.status_code} — "
        f"FastAPI should ignore unconfigured auth. Body: {resp.text}"
    )
    assert resp.status_code != 401, "Bogus Bearer token caused 401 on /reports/sales"
    assert resp.status_code != 403, "Bogus Bearer token caused 403 on /reports/sales"
