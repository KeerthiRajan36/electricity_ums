from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff
from app.models.user import User
from app.repositories.customer_repo import CustomerRepository
from app.services import report_service
from app.utils.exceptions import NotFoundException

router = APIRouter(tags=["Dashboard & Reports"])


@router.get("/dashboard/summary")
def dashboard_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return report_service.admin_dashboard_summary(db, month)


@router.get("/reports/daily-collection")
def daily_collection_report(
    day: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return report_service.daily_collection_report(db, day)


@router.get("/reports/monthly-revenue")
def monthly_revenue_report(
    month: str = Query(default_factory=lambda: date.today().strftime("%Y-%m"), pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return report_service.monthly_revenue_report(db, month)


@router.get("/reports/customer-billing/{customer_id}")
def customer_wise_billing_report(
    customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_staff)
):
    if CustomerRepository(db).get(customer_id) is None:
        raise NotFoundException("Customer not found.")
    return report_service.customer_wise_billing_report(db, customer_id)


@router.get("/reports/connection-consumption")
def connection_wise_consumption_report(db: Session = Depends(get_db), current_user: User = Depends(require_staff)):
    return report_service.connection_wise_consumption_report(db)


@router.get("/reports/technician-performance")
def technician_performance_report(db: Session = Depends(get_db), current_user: User = Depends(require_staff)):
    return report_service.technician_performance_report(db)


@router.get("/reports/complaint-resolution")
def complaint_resolution_report(db: Session = Depends(get_db), current_user: User = Depends(require_staff)):
    return report_service.complaint_resolution_report(db)


@router.get("/reports/outstanding-payments")
def outstanding_payment_report(db: Session = Depends(get_db), current_user: User = Depends(require_staff)):
    return report_service.outstanding_payment_report(db)
