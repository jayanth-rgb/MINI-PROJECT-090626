from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.services.adjustment_service import AdjustmentService
from src.application.services.dealer_service import DealerService
from src.application.services.design_grade_cb_service import DesignGradeCbService
from src.application.services.design_grade_map_service import DesignGradeMapService
from src.application.services.design_service import DesignService
from src.application.services.grade_service import GradeService
from src.application.services.inward_service import InwardService
from src.application.services.sales_service import SalesService
from src.application.services.staff_service import StaffService
from src.application.services.supplier_service import SupplierService
from src.infrastructure.db.session import get_db


def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    return SupplierService(db)


def get_staff_service(db: Session = Depends(get_db)) -> StaffService:
    return StaffService(db)


def get_dealer_service(db: Session = Depends(get_db)) -> DealerService:
    return DealerService(db)


def get_grade_service(db: Session = Depends(get_db)) -> GradeService:
    return GradeService(db)


def get_design_service(db: Session = Depends(get_db)) -> DesignService:
    return DesignService(db)


def get_design_grade_map_service(db: Session = Depends(get_db)) -> DesignGradeMapService:
    return DesignGradeMapService(db)


def get_inward_service(db: Session = Depends(get_db)) -> InwardService:
    return InwardService(db)


def get_sales_service(db: Session = Depends(get_db)) -> SalesService:
    return SalesService(db)


def get_adjustment_service(db: Session = Depends(get_db)) -> AdjustmentService:
    return AdjustmentService(db)


def get_design_grade_cb_service(db: Session = Depends(get_db)) -> DesignGradeCbService:
    return DesignGradeCbService(db)
