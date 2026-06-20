"""ST-001 — Server-side input validation (PRD non_functional.security).

Every Create payload that violates a Pydantic constraint MUST produce HTTP 422
from the API. 100% of malformed-input variants tested must be rejected.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "path,payload",
    [
        # AC-001 supplier_name empty → 422
        ("/api/v1/suppliers", {"supplier_name": "", "place": "Mallur"}),
        # AC-001 place empty → 422
        ("/api/v1/suppliers", {"supplier_name": "M", "place": ""}),
        # AC-004 staff_name empty → 422
        ("/api/v1/staff", {"staff_name": ""}),
        # AC-007 dealer_name empty → 422
        ("/api/v1/dealers", {"dealer_name": "", "place": "X"}),
        # AC-010 grade_code empty → 422
        ("/api/v1/grades", {"grade_code": ""}),
        # AC-013 size empty → 422
        ("/api/v1/designs", {"size": "", "design_name": "Ridges"}),
        # AC-013 design_name empty → 422
        ("/api/v1/designs", {"size": "16X10", "design_name": ""}),
    ],
)
def test_st001_create_with_invalid_payload_returns_422(
    client: TestClient, path: str, payload: dict
) -> None:
    response = client.post(path, json=payload)
    assert response.status_code == 422, (
        f"Expected 422 for {path} with {payload}, got {response.status_code}: "
        f"{response.text}"
    )
