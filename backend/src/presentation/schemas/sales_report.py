from datetime import date

from pydantic import BaseModel, ConfigDict


class ConsolidationRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    total_nos: int


class TransactionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sales_date: date
    dealer_id: int
    dealer_name: str
    place: str  # denormalized snapshot per DS-013 — NOT str | None
    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    nos: int


class SalesReportResponse(BaseModel):
    consolidation: list[ConsolidationRow]
    transactions: list[TransactionRow]
