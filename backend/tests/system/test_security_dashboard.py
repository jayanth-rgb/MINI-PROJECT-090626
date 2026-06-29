"""TC-132 — Dashboard security: malformed as_of_date returns 422 (F-010).

GET /api/v1/dashboard?as_of_date=not-a-date must return 422 with a response
body that references as_of_date (FastAPI date parsing error).
"""
from __future__ import annotations


def test_tc132_invalid_date_format_returns_422(client, db_session):
    """TC-132: GET /api/v1/dashboard?as_of_date=not-a-date → 422.

    FastAPI's date query parameter parser rejects non-ISO date strings with 422.
    The response body must mention the failing field (as_of_date).
    """
    resp = client.get("/api/v1/dashboard?as_of_date=not-a-date")
    assert resp.status_code == 422

    body = resp.json()
    # FastAPI 422 body contains detail list describing the parse error
    detail_str = str(body)
    assert "as_of_date" in detail_str, (
        f"Expected 'as_of_date' in response body, got: {detail_str}"
    )
