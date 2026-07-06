# T-086 — `infrastructure/exporters/excel_exporter.py` — ExcelExporter

**Module:** M-010 · **Wave:** 2 (after T-076) · **Depends on:** T-076 (schemas/inward_report.py)

## Context anchor

Same directory as T-085 (pdf_exporter). DS-021: openpyxl for XLSX. Two worksheets per workbook matching AC-065 exactly. Stateless — no DB access.

## Implementation logic

```python
# backend/src/infrastructure/exporters/excel_exporter.py
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font

from presentation.schemas.sales_report import SalesReportResponse
from presentation.schemas.inward_report import InwardReportResponse


def _write_filter_row(ws, filters: dict, col_count: int) -> None:
    summary = "Filters: All" if not filters else (
        "Filters: " + ", ".join(f"{k}: {v}" for k, v in filters.items() if v)
    )
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
    ws.cell(1, 1, summary)


def _write_headers(ws, row: int, headers: list[str]) -> None:
    bold = Font(bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row, col, h)
        cell.font = bold


class ExcelExporter:

    def export_sales_report(
        self, data: SalesReportResponse, filters: dict
    ) -> BytesIO:
        wb = Workbook()

        # Consolidation sheet
        ws_con = wb.active
        ws_con.title = "Consolidation"
        con_headers = ["Design", "Size", "Grade", "Total Nos"]
        _write_filter_row(ws_con, filters, len(con_headers))
        _write_headers(ws_con, 2, con_headers)
        for i, r in enumerate(data.consolidation, 3):
            ws_con.cell(i, 1, r.design_name)
            ws_con.cell(i, 2, r.size)
            ws_con.cell(i, 3, r.grade_code)
            ws_con.cell(i, 4, r.total_nos)

        # Transactions sheet
        ws_txn = wb.create_sheet("Transactions")
        txn_headers = ["Date", "Dealer", "Place", "Design", "Size", "Grade", "Nos"]
        _write_filter_row(ws_txn, filters, len(txn_headers))
        _write_headers(ws_txn, 2, txn_headers)
        for i, r in enumerate(data.transactions, 3):
            ws_txn.cell(i, 1, str(r.sales_date))
            ws_txn.cell(i, 2, r.dealer_name)
            ws_txn.cell(i, 3, r.place)
            ws_txn.cell(i, 4, r.design_name)
            ws_txn.cell(i, 5, r.size)
            ws_txn.cell(i, 6, r.grade_code)
            ws_txn.cell(i, 7, r.nos)

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def export_inward_report(
        self, data: InwardReportResponse, filters: dict
    ) -> BytesIO:
        wb = Workbook()

        # Consolidation sheet
        ws_con = wb.active
        ws_con.title = "Consolidation"
        con_headers = ["Design", "Size", "Grade", "Total Nos"]
        _write_filter_row(ws_con, filters, len(con_headers))
        _write_headers(ws_con, 2, con_headers)
        for i, r in enumerate(data.consolidation, 3):
            ws_con.cell(i, 1, r.design_name)
            ws_con.cell(i, 2, r.size)
            ws_con.cell(i, 3, r.grade_code)
            ws_con.cell(i, 4, r.total_nos)

        # Transactions sheet
        ws_txn = wb.create_sheet("Transactions")
        txn_headers = ["Date", "Supplier", "Place", "Design", "Size", "Grade", "Nos"]
        _write_filter_row(ws_txn, filters, len(txn_headers))
        _write_headers(ws_txn, 2, txn_headers)
        for i, r in enumerate(data.transactions, 3):
            ws_txn.cell(i, 1, str(r.purchase_date))
            ws_txn.cell(i, 2, r.supplier_name)
            ws_txn.cell(i, 3, r.place)
            ws_txn.cell(i, 4, r.design_name)
            ws_txn.cell(i, 5, r.size)
            ws_txn.cell(i, 6, r.grade_code)
            ws_txn.cell(i, 7, r.nos)

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf
```

## Constraints

- Sheet names MUST be exactly `"Consolidation"` and `"Transactions"` (AC-065 assertion).
- `wb.active` is the first sheet — set `.title = "Consolidation"` on it; create `"Transactions"` with `wb.create_sheet()`.
- `buf.seek(0)` after `wb.save(buf)` — caller reads from position 0.
- `_write_filter_row` merges cells so row 1 appears as a single summary cell.

## Do not touch

- Any other file in the repo.

## Success criteria

- **Manual**: `buf = ExcelExporter().export_inward_report(data, {}); import openpyxl; wb = openpyxl.load_workbook(buf); print(wb.sheetnames)` → `['Consolidation', 'Transactions']`
- **Automated**: TC-199: sheetnames == `['Consolidation', 'Transactions']`, sheet_count == 2.
- **DoD**: `ExcelExporter` exported with 2 methods. BytesIO at position 0. Exactly 2 sheets with exact names. No DB access.

## Checkout

> *"excel_exporter.py created. ExcelExporter with export_sales_report + export_inward_report. openpyxl 2-sheet: Consolidation + Transactions. TC-199 covered."*
