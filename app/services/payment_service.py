from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.payment import Payment, PaymentStatus
from app.repositories.bill_repo import BillRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.payment import PaymentCreate
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException


def create_payment(db: Session, bill_id: int, data: PaymentCreate) -> Payment:
    bill_repo = BillRepository(db)
    payment_repo = PaymentRepository(db)

    bill = bill_repo.get(bill_id)
    if bill is None:
        raise NotFoundException("Bill not found.")
    if bill.bill_status == BillStatus.CANCELLED:
        raise BadRequestException("Cannot pay a cancelled bill.")
    if bill.bill_status == BillStatus.PAID:
        raise BadRequestException("This bill has already been paid in full.")

    if payment_repo.get_by_transaction_id(data.transaction_id):
        raise ConflictException(f"Transaction ID '{data.transaction_id}' has already been used.")

    already_paid = Decimal(payment_repo.total_successful_for_bill(bill_id))
    remaining_due = Decimal(bill.total_amount) - already_paid
    if Decimal(data.amount) > remaining_due:
        raise BadRequestException(
            f"Payment amount {data.amount} exceeds the remaining bill balance of {remaining_due}."
        )

    # Mock payment gateway: unless the caller explicitly simulates an outcome
    # (useful for tests/demos), a payment is treated as immediately successful.
    resolved_status = data.simulate_status or PaymentStatus.SUCCESS

    payment = Payment(
        bill_id=bill_id,
        amount=data.amount,
        payment_method=data.payment_method,
        transaction_id=data.transaction_id,
        payment_status=resolved_status,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    if resolved_status == PaymentStatus.SUCCESS:
        new_total_paid = already_paid + Decimal(data.amount)
        if new_total_paid >= Decimal(bill.total_amount):
            bill.bill_status = BillStatus.PAID
            db.commit()
    # Failed payments intentionally leave bill_status untouched.

    return payment
