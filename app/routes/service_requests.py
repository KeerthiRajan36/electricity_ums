from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, get_current_user
from app.models.customer import CustomerStatus
from app.models.service_request import ServiceRequest, ServiceRequestStatus
from app.models.user import User
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.service_request_repo import ServiceRequestRepository
from app.schemas.service_request import ServiceRequestCreate, ServiceRequestRejectRequest, ServiceRequestOut
from app.services.audit_service import log_action
from app.services.notification_service import send_notification, service_request_approved
from app.utils.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])

_TERMINAL_STATUSES = {ServiceRequestStatus.APPROVED, ServiceRequestStatus.REJECTED, ServiceRequestStatus.COMPLETED}


@router.post("", response_model=ServiceRequestOut, status_code=201)
def create_service_request(
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = CustomerRepository(db).get(payload.customer_id)
    if customer is None:
        raise NotFoundException("Customer not found.")
    if customer.status == CustomerStatus.SUSPENDED:
        raise ForbiddenException("Suspended customers cannot create new service requests.")

    if payload.connection_id is not None and ConnectionRepository(db).get(payload.connection_id) is None:
        raise NotFoundException("Connection not found.")

    request = ServiceRequestRepository(db).create(payload.model_dump())
    log_action(db, current_user.id, "CREATE", "ServiceRequest", request.id, payload.request_type.value)
    return request


@router.get("", response_model=PaginatedResponse[ServiceRequestOut])
def list_service_requests(
    status: str | None = None,
    request_type: str | None = None,
    customer_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = ServiceRequestRepository(db).base_query()
    if status:
        query = query.filter(ServiceRequest.status == status)
    if request_type:
        query = query.filter(ServiceRequest.request_type == request_type)
    if customer_id:
        query = query.filter(ServiceRequest.customer_id == customer_id)
    query = apply_sorting(query, ServiceRequest, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/{request_id}", response_model=ServiceRequestOut)
def get_service_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = ServiceRequestRepository(db).get(request_id)
    if request is None:
        raise NotFoundException("Service request not found.")
    return request


def _get_pending_request(db: Session, request_id: int) -> ServiceRequest:
    request = ServiceRequestRepository(db).get(request_id)
    if request is None:
        raise NotFoundException("Service request not found.")
    if request.status in _TERMINAL_STATUSES:
        raise BadRequestException(f"Request is already '{request.status.value}' and cannot be changed further.")
    return request


@router.put("/{request_id}/approve", response_model=ServiceRequestOut)
def approve_service_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    request = _get_pending_request(db, request_id)
    request.status = ServiceRequestStatus.APPROVED
    db.commit()
    db.refresh(request)

    log_action(db, current_user.id, "UPDATE", "ServiceRequest", request.id, "Approved")
    customer_id, event, message = service_request_approved(request.customer_id, request.id)
    background_tasks.add_task(send_notification, customer_id, event, message)
    return request


@router.put("/{request_id}/reject", response_model=ServiceRequestOut)
def reject_service_request(
    request_id: int,
    payload: ServiceRequestRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    request = _get_pending_request(db, request_id)
    request.status = ServiceRequestStatus.REJECTED
    db.commit()
    db.refresh(request)

    log_action(db, current_user.id, "UPDATE", "ServiceRequest", request.id, f"Rejected: {payload.reason}")
    return request


@router.put("/{request_id}/complete", response_model=ServiceRequestOut)
def complete_service_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    request = ServiceRequestRepository(db).get(request_id)
    if request is None:
        raise NotFoundException("Service request not found.")
    if request.status != ServiceRequestStatus.APPROVED:
        raise BadRequestException("Only an approved request can be marked as completed.")

    request.status = ServiceRequestStatus.COMPLETED
    db.commit()
    db.refresh(request)

    log_action(db, current_user.id, "UPDATE", "ServiceRequest", request.id, "Completed")
    return request
