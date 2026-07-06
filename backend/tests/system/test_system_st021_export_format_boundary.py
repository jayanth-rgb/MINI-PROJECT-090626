"""ST-021 — Export format allowlist boundary (AC-066).

Accepted values (pdf, xlsx) return 200 with the correct Content-Type.
Rejected values (csv, xml, txt, json, HTML fragment, empty string) return
a 4xx. FastAPI's Query pattern check produces 422 for pattern mismatches;
the service-layer check would produce 400. Either 4xx code counts as reject.
"""
from __future__ import annotations

import pytest

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    SupplierModel,
    StaffModel,
    TradingDesignModel,
)


def _seed(db_session):
    db_session.add(TradingDesignModel(design_id=1, size="16X10", design_name="16X10 Ridges"))
    db_session.add(GradeModel(grade_id=1, grade_code="1"))
    db_session.add(SupplierModel(supplier_id=1, supplier_name="Manjunatha", place="Mallur"))
    db_session.add(StaffModel(staff_id=1, staff_name="Chandran"))
    db_session.flush()
    db_session.add(DesignGradeMapModel(design_id=1, grade_id=1))
    db_session.flush()


@pytest.mark.parametrize("fmt,ctype_prefix", [
    ("pdf", "application/pdf"),
    ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
])
@pytest.mark.parametrize("path", ["/api/v1/reports/sales/export", "/api/v1/reports/inward/export"])
def test_st021_accepted_formats_return_200(client, db_session, path, fmt, ctype_prefix):
    _seed(db_session)
    resp = client.get(path, params={"format": fmt})
    assert resp.status_code == 200, f"{path}?format={fmt} failed: {resp.text}"
    assert resp.headers["content-type"].startswith(ctype_prefix), (
        f"{path}?format={fmt} unexpected content-type: {resp.headers['content-type']}"
    )


@pytest.mark.parametrize("fmt", ["csv", "xml", "txt", "json", "<script>", ""])
@pytest.mark.parametrize("path", ["/api/v1/reports/sales/export", "/api/v1/reports/inward/export"])
def test_st021_rejected_formats_return_4xx(client, path, fmt):
    resp = client.get(path, params={"format": fmt})
    assert 400 <= resp.status_code < 500, (
        f"{path}?format={fmt!r} expected 4xx, got {resp.status_code}: {resp.text[:200]}"
    )
