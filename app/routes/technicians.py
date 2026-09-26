from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, require_admin_or_billing, get_current_user
from app.models.technician import Technician
from app.models.user import User
from app.repositories.technician_repo import TechnicianRepository
from app.schemas.technician import TechnicianCreate, TechnicianAvailabilityUpdate, TechnicianOut
from app.services.audit_service import log_action
from app.utils.exceptions import NotFoundException, ConflictException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse

router = APIRouter(prefix="/technicians", tags=["Field Technicians"])


@router.post("", response_model=TechnicianOut, status_code=201)
def create_technician(
    payload: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    repo = TechnicianRepository(db)
    if repo.get_by_employee_id(payload.employee_id):
        raise ConflictException(f"Employee ID '{payload.employee_id}' is already in use.")

    technician = repo.create(payload.model_dump())
    log_action(db, current_user.id, "CREATE", "Technician", technician.id)
    return technician


@router.get("", response_model=PaginatedResponse[TechnicianOut])
def list_technicians(
    availability_status: str | None = None,
    specialization: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = TechnicianRepository(db).base_query()
    if availability_status:
        query = query.filter(Technician.availability_status == availability_status)
    if specialization:
        query = query.filter(Technician.specialization.ilike(f"%{specialization}%"))
    query = apply_sorting(query, Technician, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/{technician_id}", response_model=TechnicianOut)
def get_technician(technician_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    technician = TechnicianRepository(db).get(technician_id)
    if technician is None:
        raise NotFoundException("Technician not found.")
    return technician


@router.put("/{technician_id}/availability", response_model=TechnicianOut)
def update_availability(
    technician_id: int,
    payload: TechnicianAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = TechnicianRepository(db)
    technician = repo.get(technician_id)
    if technician is None:
        raise NotFoundException("Technician not found.")

    technician = repo.update(technician, payload.model_dump())
    log_action(
        db, current_user.id, "UPDATE", "Technician", technician.id,
        f"Availability -> {payload.availability_status.value}",
    )
    return technician
