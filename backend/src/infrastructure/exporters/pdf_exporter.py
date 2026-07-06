from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.presentation.schemas.inward_report import InwardReportResponse
from src.presentation.schemas.sales_report import SalesReportResponse


_STYLES = getSampleStyleSheet()


def _build_filter_summary(filters: dict) -> str:
    if not filters:
        return "Filters: All"

    parts = [f"{key}: {value}" for key, value in filters.items() if value is not None]
    if not parts:
        return "Filters: All"

    return "Filters: " + ", ".join(parts)


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]
    )


class PdfExporter:
    def export_sales_report(self, data: SalesReportResponse, filters: dict) -> BytesIO:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        elements = []

        elements.append(Paragraph("Sales Report", _STYLES["Title"]))
        elements.append(Paragraph(_generated_at_text(), _STYLES["Normal"]))
        elements.append(Paragraph(_build_filter_summary(filters), _STYLES["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Consolidation", _STYLES["Heading2"]))
        consolidation_rows = [["Design", "Size", "Grade", "Total Nos"]]
        consolidation_rows.extend(
            [row.design_name, row.size, row.grade_code, str(row.total_nos)]
            for row in data.consolidation
        )
        elements.append(Table(consolidation_rows, style=_table_style()))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Transactions", _STYLES["Heading2"]))
        transaction_rows = [["Date", "Dealer", "Place", "Design", "Size", "Grade", "Nos"]]
        transaction_rows.extend(
            [
                str(row.sales_date),
                row.dealer_name,
                row.place,
                row.design_name,
                row.size,
                row.grade_code,
                str(row.nos),
            ]
            for row in data.transactions
        )
        elements.append(Table(transaction_rows, style=_table_style()))

        doc.build(elements)
        buf.seek(0)
        return buf

    def export_inward_report(self, data: InwardReportResponse, filters: dict) -> BytesIO:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        elements = []

        elements.append(Paragraph("Inward Report", _STYLES["Title"]))
        elements.append(Paragraph(_generated_at_text(), _STYLES["Normal"]))
        elements.append(Paragraph(_build_filter_summary(filters), _STYLES["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Consolidation", _STYLES["Heading2"]))
        consolidation_rows = [["Design", "Size", "Grade", "Total Nos"]]
        consolidation_rows.extend(
            [row.design_name, row.size, row.grade_code, str(row.total_nos)]
            for row in data.consolidation
        )
        elements.append(Table(consolidation_rows, style=_table_style()))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Transactions", _STYLES["Heading2"]))
        transaction_rows = [["Date", "Supplier", "Place", "Design", "Size", "Grade", "Nos"]]
        transaction_rows.extend(
            [
                str(row.purchase_date),
                row.supplier_name,
                row.place,
                row.design_name,
                row.size,
                row.grade_code,
                str(row.nos),
            ]
            for row in data.transactions
        )
        elements.append(Table(transaction_rows, style=_table_style()))

        doc.build(elements)
        buf.seek(0)
        return buf


def _generated_at_text() -> str:
    return f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
