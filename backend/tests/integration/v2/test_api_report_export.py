"""V2 TC-215, TC-216 — GET /reports/{sales,inward}/export routers."""
from __future__ import annotations

from tests.integration.v2._helpers import bearer, seed_user


def test_tc215_export_sales_pdf_returns_200_with_pdf_content_type(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    resp = client.get(
        "/api/v1/reports/sales/export",
        params={"format": "pdf"},
        headers=bearer("admin", "SUPERVISOR"),
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert len(resp.content) > 0
    assert "attachment" in resp.headers.get("content-disposition", "")


def test_tc216_export_inward_xlsx_returns_200_with_xlsx_content_type(client, db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    resp = client.get(
        "/api/v1/reports/inward/export",
        params={"format": "xlsx"},
        headers=bearer("admin", "SUPERVISOR"),
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(resp.content) > 0
