from datetime import date
from pydantic import BaseModel, ConfigDict


class InwardConsolidationRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    total_nos: int


class InwardTransactionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    purchase_date: date
    supplier_id: int
    supplier_name: str
    place: str  # DS-013: snapshot from tbl_inward_header.place
    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    nos: int


class InwardReportResponse(BaseModel):
    consolidation: list[InwardConsolidationRow]
    transactions: list[InwardTransactionRow]
