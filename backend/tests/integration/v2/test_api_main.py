"""V2 TC-213 — global auth guard on V1 routers (main.py include_router deps)."""
from __future__ import annotations


def test_tc213_unauthenticated_v1_endpoint_returns_401(unauthenticated_client):
    resp = unauthenticated_client.get("/api/v1/suppliers")
    assert resp.status_code == 401
