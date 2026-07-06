"""ST-002 — V1 endpoints require JWT (DS-025 supersedes DS-005).

Original ST-002 asserted DS-005 (V1 has no auth). V2 T-092 attached a
mount-level ``Depends(get_current_user)`` to all 11 V1 routers, and TC-213
asserts the new contract: any unauthenticated V1 request returns 401.
This scenario now regression-guards the inverse invariant — a missing
Authorization header on any V1 master GET must be rejected with 401 and a
``WWW-Authenticate: Bearer`` challenge (RFC 6750).
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
def test_st002_list_endpoints_require_auth(
    unauthenticated_client: TestClient, path: str
) -> None:
    response = unauthenticated_client.get(path)
    assert response.status_code == 401, (
        f"V1 endpoint {path} returned {response.status_code} without an "
        f"Authorization header — DS-025 says V1 requires JWT auth."
    )
    assert response.headers.get("WWW-Authenticate") == "Bearer", (
        f"V1 endpoint {path} returned 401 without WWW-Authenticate: Bearer "
        f"challenge — violates RFC 6750."
    )
