from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, get_current_user
from app.models.meter import MeterStatus
from app.models.reading import MeterReading
from app.models.user import User
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.meter_repo import MeterRepository
from app.repositories.reading_repo import ReadingRepository
from app.schemas.reading import MeterReadingCreate, MeterReadingOut
from app.services.audit_service import log_action
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException

router = APIRouter(tags=["Meter Readings"])


@router.post("/meter-readings", response_model=MeterReadingOut, status_code=201)
def create_reading(
    payload: MeterReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    meter_repo = MeterRepository(db)
    reading_repo = ReadingRepository(db)

    meter = meter_repo.get(payload.meter_id)
    if meter is None:
        raise NotFoundException("Meter not found.")
    if meter.meter_status != MeterStatus.ACTIVE:
        raise BadRequestException("Only active meters can receive readings.")

    if reading_repo.exists_for_period(payload.meter_id, payload.billing_period):
        raise ConflictException(
            f"A reading for meter {payload.meter_id} in period {payload.billing_period} already exists."
        )

    previous_reading = Decimal(meter.current_reading)
    current_reading = Decimal(payload.current_reading)

    if current_reading < previous_reading:
        raise BadRequestException("Current reading cannot be lower than the previous reading.")

    units_consumed = current_reading - previous_reading
    if units_consumed < 0:
        raise BadRequestException("Negative consumption is not allowed.")

    reading = MeterReading(
        meter_id=payload.meter_id,
        reading_date=payload.reading_date,
        previous_reading=previous_reading,
        current_reading=current_reading,
        units_consumed=units_consumed,
        reading_source=payload.reading_source,
        remarks=payload.remarks,
        billing_period=payload.billing_period,
    )
    db.add(reading)

    meter.current_reading = current_reading
    db.commit()
    db.refresh(reading)

    log_action(db, current_user.id, "CREATE", "MeterReading", reading.id)
    return reading


@router.get("/meter-readings", response_model=list[MeterReadingOut])
def list_readings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ReadingRepository(db).get_all()


@router.get("/meters/{meter_id}/readings", response_model=list[MeterReadingOut])
def readings_for_meter(meter_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if MeterRepository(db).get(meter_id) is None:
        raise NotFoundException("Meter not found.")
    return ReadingRepository(db).get_for_meter(meter_id)


@router.get("/connections/{connection_id}/readings", response_model=list[MeterReadingOut])
def readings_for_connection(
    connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if ConnectionRepository(db).get(connection_id) is None:
        raise NotFoundException("Connection not found.")
    return ReadingRepository(db).get_for_connection(connection_id)
