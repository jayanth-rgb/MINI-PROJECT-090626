# T-085 — `infrastructure/exporters/pdf_exporter.py` — PdfExporter

**Module:** M-010 · **Wave:** 2 (after T-076) · **Depends on:** T-076 (schemas/inward_report.py)

## Context anchor

Directory `backend/src/infrastructure/exporters/` + `__init__.py` created by sprint-scaffold (DEP-V2-001 resolution). DS-021: reportlab for PDF, StreamingResponse. Stateless — pure function calls, no DB. `export_sales_report` uses `SalesReportResponse` (S3 T-058); `export_inward_report` uses `InwardReportResponse` (T-076 this sprint).

## Implementation logic

```python
# backend/src/infrastructure/exporters/pdf_exporter.py
from datetime import datetime
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from presentation.schemas.sales_report import SalesReportResponse
from presentation.schemas.inward_report import InwardReportResponse


_STYLES = getSampleStyleSheet()


def _build_filter_summary(filters: dict) -> str:
    if not filters:
        return "Filters: All"
    parts = [f"{k}: {v}" for k, v in filters.items() if v is not None]
    return "Filters: " + ", ".join(parts) if parts else "Filters: All"


class PdfExporter:

    def export_sales_report(
        self, data: SalesReportResponse, filters: dict
    ) -> BytesIO:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        elements = []
        styles = _STYLES

        elements.append(Paragraph("Sales Report", styles["Title"]))
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
        elements.append(Paragraph(_build_filter_summary(filters), styles["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Consolidation", styles["Heading2"]))
        con_data = [["Design", "Size", "Grade", "Total Nos"]] + [
            [r.design_name, r.size, r.grade_code, str(r.total_nos)]
            for r in data.consolidation
        ]
        elements.append(Table(con_data, style=_table_style()))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Transactions", styles["Heading2"]))
        txn_data = [["Date", "Dealer", "Place", "Design", "Size", "Grade", "Nos"]] + [
            [str(r.sales_date), r.dealer_name, r.place, r.design_name, r.size, r.grade_code, str(r.nos)]
            for r in data.transactions
        ]
        elements.append(Table(txn_data, style=_table_style()))

        doc.build(elements)
        buf.seek(0)
        return buf

    def export_inward_report(
        self, data: InwardReportResponse, filters: dict
    ) -> BytesIO:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        elements = []
        styles = _STYLES

        elements.append(Paragraph("Inward Report", styles["Title"]))
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
        elements.append(Paragraph(_build_filter_summary(filters), styles["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Consolidation", styles["Heading2"]))
        con_data = [["Design", "Size", "Grade", "Total Nos"]] + [
            [r.design_name, r.size, r.grade_code, str(r.total_nos)]
            for r in data.consolidation
        ]
        elements.append(Table(con_data, style=_table_style()))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Transactions", styles["Heading2"]))
        txn_data = [["Date", "Supplier", "Place", "Design", "Size", "Grade", "Nos"]] + [
            [str(r.purchase_date), r.supplier_name, r.place, r.design_name, r.size, r.grade_code, str(r.nos)]
            for r in data.transactions
        ]
        elements.append(Table(txn_data, style=_table_style()))

        doc.build(elements)
        buf.seek(0)
        return buf


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ])
```

## Constraints

- `buf.seek(0)` MUST be called before returning — the caller reads from position 0.
- Use `BytesIO()` not a temp file — the doc must never touch the filesystem.
- `doc.build(elements)` writes PDF to the `BytesIO` buffer passed to `SimpleDocTemplate`.
- `_table_style` is a module-level helper (not a method) — both methods call it to keep styling consistent.
- Empty lists for consolidation/transactions produce valid PDF with empty tables (valid output per AC-061).

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `from src.infrastructure.exporters.pdf_exporter import PdfExporter; from io import BytesIO; ...` → `buf.read(5) == b'%PDF-'`
- **Automated**: TC-198: first 5 bytes == `b'%PDF-'`, size > 0.
- **DoD**: `PdfExporter` exported with 2 methods. Returns `BytesIO` at position 0. PDF magic bytes present. No DB access.

## Checkout

> *"pdf_exporter.py created. PdfExporter with export_sales_report + export_inward_report. reportlab SimpleDocTemplate. TC-198 covered."*
