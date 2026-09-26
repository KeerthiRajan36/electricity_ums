from datetime import date
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_or_billing, get_current_user
from app.models.bill import Bill, BillStatus
from app.models.user import User
from app.repositories.bill_repo import BillRepository
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.customer_repo import CustomerRepository
from app.schemas.bill import BillGenerateRequest, BillOut
from app.services import billing_service
from app.services.audit_service import log_action
from app.services.notification_service import send_notification, bill_generated
from app.utils.exceptions import NotFoundException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse

router = APIRouter(tags=["Bills"])


@router.post("/bills/generate", response_model=BillOut, status_code=201)
def generate_bill(
    payload: BillGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    bill = billing_service.generate_bill(db, payload)
    log_action(db, current_user.id, "CREATE", "Bill", bill.id)

    connection = ConnectionRepository(db).get(bill.connection_id)
    if connection:
        customer_id, event, message = bill_generated(connection.customer_id, bill.id, bill.total_amount)
        background_tasks.add_task(send_notification, customer_id, event, message)

    return bill


@router.get("/bills", response_model=PaginatedResponse[BillOut])
def list_bills(
    billing_month: str | None = None,
    bill_status: str | None = None,
    overdue_only: bool = False,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = BillRepository(db)
    effective_status = BillStatus.OVERDUE.value if overdue_only else bill_status
    query = repo.filtered_query(billing_month, effective_status, min_amount, max_amount)
    query = apply_sorting(query, Bill, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/bills/{bill_id}", response_model=BillOut)
def get_bill(bill_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bill = BillRepository(db).get(bill_id)
    if bill is None:
        raise NotFoundException("Bill not found.")
    return bill


@router.get("/customers/{customer_id}/bills", response_model=list[BillOut])
def bills_for_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if CustomerRepository(db).get(customer_id) is None:
        raise NotFoundException("Customer not found.")
    return BillRepository(db).get_for_customer(customer_id)


@router.get("/connections/{connection_id}/bills", response_model=list[BillOut])
def bills_for_connection(
    connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if ConnectionRepository(db).get(connection_id) is None:
        raise NotFoundException("Connection not found.")
    return BillRepository(db).get_for_connection(connection_id)


@router.post("/bills/process-overdue", response_model=list[BillOut])
def process_overdue_bills(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    """
    Manually triggers overdue processing (Level 15 bonus: 'Automated overdue
    bill processing'). In production this same service function would be
    invoked by a Celery-beat schedule or cron job instead of an HTTP call.
    """
    updated_bills = billing_service.process_overdue_bills(db)
    for bill in updated_bills:
        connection = ConnectionRepository(db).get(bill.connection_id)
        if connection:
            from app.services.notification_service import bill_overdue

            customer_id, event, message = bill_overdue(connection.customer_id, bill.id)
            background_tasks.add_task(send_notification, customer_id, event, message)
    log_action(db, current_user.id, "UPDATE", "Bill", None, f"Processed {len(updated_bills)} overdue bills")
    return updated_bills
