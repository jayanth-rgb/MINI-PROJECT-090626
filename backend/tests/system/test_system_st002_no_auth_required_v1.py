"""ST-002 — V1 endpoints are unauthenticated (DS-005 / R-004 non-regression).

If an Authorization middleware were ever accidentally added to V1, every
endpoint would fail with 401/403 without credentials. This scenario asserts
the V1 invariant explicitly: each master GET endpoint returns 2xx with NO
Authorization header.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/suppliers",
        "/api/v1/staff",
        "/api/v1/dealers",
        "/api/v1/grades",
        "/api/v1/designs",
        "/api/v1/design-grade-map",
    ],
)
def test_st002_list_endpoints_no_auth_required(
    client: TestClient, path: str
) -> None:
    response = client.get(path)
    assert response.status_code < 300, (
        f"V1 endpoint {path} returned {response.status_code} without an "
        f"Authorization header — DS-005 says no auth should be required."
    )
    assert response.status_code != 401
    assert response.status_code != 403
