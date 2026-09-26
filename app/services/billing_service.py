from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.models.bill import Bill, BillStatus
from app.models.connection import ConnectionStatus
from app.repositories.bill_repo import BillRepository
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.meter_repo import MeterRepository
from app.repositories.reading_repo import ReadingRepository
from app.schemas.bill import BillGenerateRequest
from app.services.tariff_service import calculate_slab_charge
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException


def generate_bill(db: Session, data: BillGenerateRequest) -> Bill:
    connection_repo = ConnectionRepository(db)
    bill_repo = BillRepository(db)
    meter_repo = MeterRepository(db)
    reading_repo = ReadingRepository(db)

    connection = connection_repo.get(data.connection_id)
    if connection is None:
        raise NotFoundException("Connection not found.")
    if connection.status == ConnectionStatus.DISCONNECTED:
        raise BadRequestException("Disconnected connections cannot generate new bills.")

    if bill_repo.get_for_connection_and_month(data.connection_id, data.billing_month):
        raise ConflictException(
            f"A bill for connection {data.connection_id} and month {data.billing_month} already exists."
        )

    meter = meter_repo.get_active_for_connection(data.connection_id)
    if meter is None:
        raise BadRequestException("No active meter found for this connection.")

    reading = next(
        (r for r in reading_repo.get_for_meter(meter.id) if r.billing_period == data.billing_month), None
    )
    if reading is None:
        raise BadRequestException(
            f"No meter reading recorded for billing period {data.billing_month}. "
            "Record a meter reading before generating the bill."
        )

    units_consumed = Decimal(reading.units_consumed)
    energy_charge, fixed_charge = calculate_slab_charge(
        db, connection.connection_type.value, units_consumed, data.billing_month
    )

    tax = ((energy_charge + fixed_charge) * Decimal(settings.TAX_PERCENTAGE) / Decimal("100")).quantize(
        Decimal("0.01")
    )
    late_fee = Decimal("0")
    discount = Decimal(data.discount)

    total_amount = energy_charge + fixed_charge + tax + late_fee - discount
    if total_amount <= 0:
        raise BadRequestException("Computed bill amount must be greater than 0.")

    due_date = date.today() + timedelta(days=settings.BILL_DUE_DAYS)

    bill = Bill(
        connection_id=connection.id,
        billing_month=data.billing_month,
        units_consumed=units_consumed,
        energy_charge=energy_charge,
        fixed_charge=fixed_charge,
        tax=tax,
        late_fee=late_fee,
        discount=discount,
        total_amount=total_amount,
        due_date=due_date,
        bill_status=BillStatus.GENERATED,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def process_overdue_bills(db: Session) -> list[Bill]:
    """
    Marks bills whose due_date has passed and which are still unpaid as
    OVERDUE, applying the configured flat late fee. Intended to be run on a
    schedule (a Celery-beat task or cron-triggered endpoint hit in production;
    here it is exposed as an admin-triggered endpoint — see README).
    """
    today = date.today()
    bill_repo = BillRepository(db)
    candidates = (
        bill_repo.base_query()
        .filter(
            Bill.due_date < today,
            Bill.bill_status.in_([BillStatus.GENERATED, BillStatus.PENDING]),
        )
        .all()
    )

    updated = []
    for bill in candidates:
        bill.late_fee = Decimal(bill.late_fee) + Decimal(settings.LATE_FEE_FLAT_AMOUNT)
        bill.total_amount = Decimal(bill.total_amount) + Decimal(settings.LATE_FEE_FLAT_AMOUNT)
        bill.bill_status = BillStatus.OVERDUE
        updated.append(bill)

    db.commit()
    for bill in updated:
        db.refresh(bill)
    return updated
