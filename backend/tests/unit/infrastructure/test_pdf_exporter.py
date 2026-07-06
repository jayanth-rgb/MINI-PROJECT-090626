"""V2 TC-198 — PdfExporter.export_sales_report emits a valid PDF header (%PDF-)."""
from __future__ import annotations

from datetime import date

from src.infrastructure.exporters.pdf_exporter import PdfExporter
from src.presentation.schemas.sales_report import (
    ConsolidationRow,
    SalesReportResponse,
    TransactionRow,
)


def test_tc198_pdf_exporter_sales_report_starts_with_pdf_magic():
    data = SalesReportResponse(
        consolidation=[
            ConsolidationRow(
                design_id=1,
                design_name="16X10 Ridges",
                size="16X10",
                grade_id=1,
                grade_code="1",
                total_nos=100,
            )
        ],
        transactions=[
            TransactionRow(
                sales_date=date(2026, 7, 1),
                dealer_id=1,
                dealer_name="Raj Hardwares",
                place="Dindivanam",
                design_id=1,
                design_name="16X10 Ridges",
                size="16X10",
                grade_id=1,
                grade_code="1",
                nos=100,
            )
        ],
    )
    buf = PdfExporter().export_sales_report(data, {})
    payload = buf.getvalue()
    assert payload[:5] == b"%PDF-"
    assert len(payload) > 0
