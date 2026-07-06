"""V2 TC-200 — ReportExportService rejects unsupported export format with HTTP 400."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.application.services.report_export_service import ReportExportService


def test_tc200_export_sales_csv_format_raises_http_400():
    svc = ReportExportService(db=None)  # _validate_format is static and needs no DB.
    with pytest.raises(HTTPException) as exc_info:
        svc.export_sales(
            format="csv",
            date_from=None,
            date_to=None,
            dealer_ids=None,
            places=None,
            design_ids=None,
        )
    assert exc_info.value.status_code == 400
