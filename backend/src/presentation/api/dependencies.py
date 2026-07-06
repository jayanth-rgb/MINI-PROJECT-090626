from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.services.adjustment_service import AdjustmentService
from src.application.services.dashboard_service import DashboardService
from src.application.services.dealer_service import DealerService
from src.application.services.design_grade_cb_service import DesignGradeCbService
from src.application.services.design_grade_map_service import DesignGradeMapService
from src.application.services.design_service import DesignService
from src.application.services.grade_service import GradeService
from src.application.services.inward_service import InwardService
from src.application.services.sales_report_service import SalesReportService
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


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_sales_report_service(db: Session = Depends(get_db)) -> SalesReportService:
    return SalesReportService(db)


# ---------------------------------------------------------------------------
# V2 additions — auth guards + V2 service DI factories (T-089)
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status  # noqa: E402 — appended per T-089 append-only rule
from fastapi.security import OAuth2PasswordBearer

from src.domain.auth import decode_access_token
from src.infrastructure.db.repositories.auth import UserRepository
from src.application.services.auth_service import AuthService
from src.application.services.inward_report_service import InwardReportService
from src.application.services.pricing_service import PricingService
from src.application.services.invoice_service import InvoiceService
from src.application.services.report_export_service import ReportExportService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Validate Bearer JWT and return the active UserModel.

    Re-fetches is_active from DB on every call (DS-018) so deactivation takes
    effect immediately without waiting for token expiry.
    Raises HTTP 401 with WWW-Authenticate: Bearer on any failure (RFC 6750).
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = UserRepository(db).get_by_username(username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_supervisor(
    current_user=Depends(get_current_user),
):
    """Raise HTTP 403 if the authenticated user is not a SUPERVISOR (DS-019).

    FastAPI deduplicates get_current_user within a single request, so the DB
    lookup runs only once regardless of how many dependencies chain from it.
    """
    if current_user.role != "SUPERVISOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUPERVISOR role required",
        )
    return current_user


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_inward_report_service(db: Session = Depends(get_db)) -> InwardReportService:
    return InwardReportService(db)


def get_pricing_service(db: Session = Depends(get_db)) -> PricingService:
    return PricingService(db)


def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db)


def get_report_export_service(db: Session = Depends(get_db)) -> ReportExportService:
    return ReportExportService(db)
