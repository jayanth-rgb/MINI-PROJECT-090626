from pydantic import BaseModel, ConfigDict


class DashboardRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    design_id: int
    design_name: str
    size: str
    grade_id: int
    grade_code: str
    opening: int
    inward: int
    outward: int
    adjust: int
    closing: int
