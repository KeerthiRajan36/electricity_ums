from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, get_current_user
from app.models.meter import Meter, MeterStatus
from app.models.user import User
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.meter_repo import MeterRepository
from app.schemas.meter import MeterCreate, MeterUpdate, MeterReplaceRequest, MeterOut
from app.services.audit_service import log_action
from app.services.notification_service import send_notification, meter_replacement_completed
from app.utils.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse
from fastapi import BackgroundTasks

router = APIRouter(prefix="/meters", tags=["Meters"])


@router.post("", response_model=MeterOut, status_code=201)
def create_meter(
    payload: MeterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    connection = ConnectionRepository(db).get(payload.connection_id)
    if connection is None:
        raise NotFoundException("Connection not found.")

    repo = MeterRepository(db)
    if repo.get_by_meter_number(payload.meter_number):
        raise ConflictException(f"Meter number '{payload.meter_number}' already exists.")
    if repo.get_active_for_connection(payload.connection_id):
        raise ConflictException("This connection already has an active meter.")

    data = payload.model_dump()
    data["current_reading"] = data["initial_reading"]
    meter = repo.create(data)
    log_action(db, current_user.id, "CREATE", "Meter", meter.id)
    return meter


@router.get("", response_model=PaginatedResponse[MeterOut])
def list_meters(
    meter_status: str | None = None,
    connection_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = MeterRepository(db)
    query = repo.base_query()
    if meter_status:
        query = query.filter(Meter.meter_status == meter_status)
    if connection_id:
        query = query.filter(Meter.connection_id == connection_id)
    query = apply_sorting(query, Meter, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/{meter_id}", response_model=MeterOut)
def get_meter(meter_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meter = MeterRepository(db).get(meter_id)
    if meter is None:
        raise NotFoundException("Meter not found.")
    return meter


@router.put("/{meter_id}", response_model=MeterOut)
def update_meter(
    meter_id: int,
    payload: MeterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = MeterRepository(db)
    meter = repo.get(meter_id)
    if meter is None:
        raise NotFoundException("Meter not found.")
    meter = repo.update(meter, payload.model_dump(exclude_unset=True))
    log_action(db, current_user.id, "UPDATE", "Meter", meter.id)
    return meter


@router.post("/{meter_id}/replace", response_model=MeterOut)
def replace_meter(
    meter_id: int,
    payload: MeterReplaceRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = MeterRepository(db)
    old_meter = repo.get(meter_id)
    if old_meter is None:
        raise NotFoundException("Meter not found.")
    if repo.get_by_meter_number(payload.new_meter_number):
        raise ConflictException(f"Meter number '{payload.new_meter_number}' already exists.")

    old_meter.meter_status = MeterStatus.REMOVED
    db.commit()

    new_meter = Meter(
        connection_id=old_meter.connection_id,
        meter_number=payload.new_meter_number,
        meter_type=payload.new_meter_type,
        installation_date=payload.installation_date,
        initial_reading=payload.initial_reading,
        current_reading=payload.initial_reading,
        meter_status=MeterStatus.ACTIVE,
    )
    db.add(new_meter)
    db.commit()
    db.refresh(new_meter)

    log_action(db, current_user.id, "UPDATE", "Meter", old_meter.id, f"Replaced by meter {new_meter.meter_number}")

    connection = ConnectionRepository(db).get(new_meter.connection_id)
    if connection:
        customer_id, event, message = meter_replacement_completed(connection.customer_id, new_meter.meter_number)
        background_tasks.add_task(send_notification, customer_id, event, message)

    return new_meter
