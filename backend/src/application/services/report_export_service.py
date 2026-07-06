"""M-010 Report Export Service — F-016 orchestration layer.

Validates the requested export format, delegates to the appropriate report
service to obtain data, then routes to PdfExporter or ExcelExporter based on
the format param. Returns a (BytesIO, content_type, filename) 3-tuple so the
presentation layer can wrap it in a StreamingResponse without buffering the
full file.

DS-007: application layer — no SQLAlchemy queries here; all data access goes
through SalesReportService / InwardReportService (their own repositories).
DS-021: reportlab for PDF, openpyxl for XLSX.
"""

from datetime import date
from io import BytesIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.application.services.inward_report_service import InwardReportService
from src.application.services.sales_report_service import SalesReportService
from src.infrastructure.exporters.excel_exporter import ExcelExporter
from src.infrastructure.exporters.pdf_exporter import PdfExporter

_PDF_MIME = "application/pdf"
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_SUPPORTED_FORMATS = ("pdf", "xlsx")


class ReportExportService:
    """M-010: orchestrates report data retrieval + format routing (DS-021)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_sales(
        self,
        format: str,
        date_from: date | None = None,
        date_to: date | None = None,
        dealer_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> tuple[BytesIO, str, str]:
        """Generate and export the Sales Report in the requested format.

        Format validation is performed FIRST (fail-fast) before any DB call.

        Args:
            format: 'pdf' or 'xlsx' — anything else raises HTTPException 400.
            date_from: optional filter lower bound (inclusive).
            date_to: optional filter upper bound (inclusive).
            dealer_ids: optional list of dealer IDs to include.
            places: optional list of place names to include.
            design_ids: optional list of design IDs to include.

        Returns:
            (BytesIO, content_type, filename) — caller wraps in StreamingResponse.

        Raises:
            HTTPException 400: if format is not 'pdf' or 'xlsx'.
        """
        self._validate_format(format)

        filters = dict(
            date_from=date_from,
            date_to=date_to,
            dealer_ids=dealer_ids,
            places=places,
            design_ids=design_ids,
        )

        data = SalesReportService(self._db).generate(
            date_from=date_from,
            date_to=date_to,
            dealer_ids=dealer_ids,
            places=places,
            design_ids=design_ids,
        )

        today_str = date.today().strftime("%Y-%m-%d")

        if format == "pdf":
            buf = PdfExporter().export_sales_report(data, filters)
            return buf, _PDF_MIME, f"sales_report_{today_str}.pdf"
        else:
            buf = ExcelExporter().export_sales_report(data, filters)
            return buf, _XLSX_MIME, f"sales_report_{today_str}.xlsx"

    def export_inward(
        self,
        format: str,
        date_from: date | None = None,
        date_to: date | None = None,
        supplier_ids: list[int] | None = None,
        places: list[str] | None = None,
        design_ids: list[int] | None = None,
    ) -> tuple[BytesIO, str, str]:
        """Generate and export the Inward Report in the requested format.

        Format validation is performed FIRST (fail-fast) before any DB call.

        Args:
            format: 'pdf' or 'xlsx' — anything else raises HTTPException 400.
            date_from: optional filter lower bound (inclusive).
            date_to: optional filter upper bound (inclusive).
            supplier_ids: optional list of supplier IDs to include.
            places: optional list of place names to include.
            design_ids: optional list of design IDs to include.

        Returns:
            (BytesIO, content_type, filename) — caller wraps in StreamingResponse.

        Raises:
            HTTPException 400: if format is not 'pdf' or 'xlsx'.
        """
        self._validate_format(format)

        filters = dict(
            date_from=date_from,
            date_to=date_to,
            supplier_ids=supplier_ids,
            places=places,
            design_ids=design_ids,
        )

        data = InwardReportService(self._db).generate(
            date_from=date_from,
            date_to=date_to,
            supplier_ids=supplier_ids,
            places=places,
            design_ids=design_ids,
        )

        today_str = date.today().strftime("%Y-%m-%d")

        if format == "pdf":
            buf = PdfExporter().export_inward_report(data, filters)
            return buf, _PDF_MIME, f"inward_report_{today_str}.pdf"
        else:
            buf = ExcelExporter().export_inward_report(data, filters)
            return buf, _XLSX_MIME, f"inward_report_{today_str}.xlsx"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_format(format: str) -> None:
        """Raise HTTPException 400 if format is not in the supported set.

        TC-200 covers the csv → 400 path.
        """
        if format not in _SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{format}'. Supported formats: {list(_SUPPORTED_FORMATS)}.",
            )
