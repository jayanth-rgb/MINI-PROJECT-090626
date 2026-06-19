"""API contract test for /api/v1/grades — duplicate grade_code → 409.

Covers: TC-035.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_tc035_post_grades_duplicate_code_returns_409_on_second(
    client: TestClient,
) -> None:
    first = client.post("/api/v1/grades", json={"grade_code": "1"})
    assert first.status_code == 201

    second = client.post("/api/v1/grades", json={"grade_code": "1"})

    assert second.status_code == 409
    detail = second.json().get("detail", "")
    assert "grade_code" in detail
