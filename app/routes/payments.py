from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.payment import PaymentStatus
from app.models.user import User
from app.repositories.bill_repo import BillRepository
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services import payment_service
from app.services.audit_service import log_action
from app.services.notification_service import send_notification, payment_success, payment_failure
from app.utils.exceptions import NotFoundException

router = APIRouter(tags=["Payments"])


@router.post("/payments/{bill_id}", response_model=PaymentOut, status_code=201)
def make_payment(
    bill_id: int,
    payload: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = payment_service.create_payment(db, bill_id, payload)
    log_action(db, current_user.id, "CREATE", "Payment", payment.id)

    bill = BillRepository(db).get(bill_id)
    connection = ConnectionRepository(db).get(bill.connection_id) if bill else None
    if connection:
        if payment.payment_status == PaymentStatus.SUCCESS:
            customer_id, event, message = payment_success(connection.customer_id, bill_id, payment.amount)
        else:
            customer_id, event, message = payment_failure(connection.customer_id, bill_id, payment.amount)
        background_tasks.add_task(send_notification, customer_id, event, message)

    return payment


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return PaymentRepository(db).get_all()


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payment = PaymentRepository(db).get(payment_id)
    if payment is None:
        raise NotFoundException("Payment not found.")
    return payment


@router.get("/bills/{bill_id}/payments", response_model=list[PaymentOut])
def payments_for_bill(bill_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if BillRepository(db).get(bill_id) is None:
        raise NotFoundException("Bill not found.")
    return PaymentRepository(db).get_for_bill(bill_id)
