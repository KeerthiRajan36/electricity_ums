from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, get_current_user
from app.models.complaint import Complaint, ComplaintHistory, ComplaintStatus
from app.models.technician import AvailabilityStatus
from app.models.user import User
from app.repositories.complaint_repo import ComplaintRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.technician_repo import TechnicianRepository
from app.schemas.complaint import (
    ComplaintCreate, ComplaintAssignRequest, ComplaintStatusUpdateRequest, ComplaintOut, ComplaintHistoryOut
)
from app.services.audit_service import log_action
from app.services.notification_service import send_notification, complaint_assigned, complaint_resolved
from app.utils.exceptions import NotFoundException, BadRequestException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _add_history(db: Session, complaint_id: int, event: str, actor_user_id: int | None):
    db.add(ComplaintHistory(complaint_id=complaint_id, event=event, actor_user_id=actor_user_id))
    db.commit()


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if CustomerRepository(db).get(payload.customer_id) is None:
        raise NotFoundException("Customer not found.")

    complaint = ComplaintRepository(db).create(payload.model_dump())
    _add_history(db, complaint.id, f"Complaint created with priority={complaint.priority.value}", current_user.id)
    log_action(db, current_user.id, "CREATE", "Complaint", complaint.id)
    return complaint


@router.get("", response_model=PaginatedResponse[ComplaintOut])
def list_complaints(
    priority: str | None = None,
    status: str | None = None,
    complaint_type: str | None = None,
    assigned_to: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ComplaintRepository(db)
    query = repo.filtered_query(priority, status, complaint_type, assigned_to)
    # Emergency complaints surface first by default when no explicit sort is requested.
    if not sort_by:
        from sqlalchemy import case

        priority_rank = case(
            (Complaint.priority == "emergency", 0),
            (Complaint.priority == "high", 1),
            (Complaint.priority == "medium", 2),
            else_=3,
        )
        query = query.order_by(priority_rank, Complaint.created_at)
    else:
        query = apply_sorting(query, Complaint, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    complaint = ComplaintRepository(db).get(complaint_id)
    if complaint is None:
        raise NotFoundException("Complaint not found.")
    return complaint


@router.get("/{complaint_id}/history", response_model=list[ComplaintHistoryOut])
def complaint_history(complaint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    complaint = ComplaintRepository(db).get(complaint_id)
    if complaint is None:
        raise NotFoundException("Complaint not found.")
    return complaint.history


@router.put("/{complaint_id}/assign", response_model=ComplaintOut)
def assign_complaint(
    complaint_id: int,
    payload: ComplaintAssignRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    complaint = ComplaintRepository(db).get(complaint_id)
    if complaint is None:
        raise NotFoundException("Complaint not found.")

    technician_repo = TechnicianRepository(db)
    technician = technician_repo.get(payload.technician_id)
    if technician is None:
        raise NotFoundException("Technician not found.")
    if technician.availability_status != AvailabilityStatus.AVAILABLE:
        raise BadRequestException("Only available technicians can be assigned.")

    complaint.assigned_to = technician.id
    complaint.status = ComplaintStatus.ASSIGNED
    technician.availability_status = AvailabilityStatus.BUSY
    db.commit()
    db.refresh(complaint)

    _add_history(db, complaint.id, f"Assigned to technician {technician.name}", current_user.id)
    log_action(db, current_user.id, "UPDATE", "Complaint", complaint.id, f"Assigned to {technician.id}")

    customer_id, event, message = complaint_assigned(complaint.customer_id, complaint.id, technician.name)
    background_tasks.add_task(send_notification, customer_id, event, message)

    return complaint


@router.put("/{complaint_id}/status", response_model=ComplaintOut)
def update_complaint_status(
    complaint_id: int,
    payload: ComplaintStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    complaint = ComplaintRepository(db).get(complaint_id)
    if complaint is None:
        raise NotFoundException("Complaint not found.")

    complaint.status = payload.status

    # Freeing the technician once work is done/closed.
    if payload.status in (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED) and complaint.assigned_to:
        technician = TechnicianRepository(db).get(complaint.assigned_to)
        if technician:
            technician.availability_status = AvailabilityStatus.AVAILABLE

    db.commit()
    db.refresh(complaint)

    _add_history(db, complaint.id, f"Status changed to {payload.status.value}", current_user.id)
    log_action(db, current_user.id, "UPDATE", "Complaint", complaint.id, f"Status -> {payload.status.value}")

    if payload.status == ComplaintStatus.RESOLVED:
        customer_id, event, message = complaint_resolved(complaint.customer_id, complaint.id)
        background_tasks.add_task(send_notification, customer_id, event, message)

    return complaint
