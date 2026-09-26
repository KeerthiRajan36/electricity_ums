from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, require_admin_or_billing, get_current_user
from app.models.connection import Connection, ConnectionStatus
from app.models.user import User
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.customer_repo import CustomerRepository
from app.schemas.connection import ConnectionCreate, ConnectionUpdate, ConnectionOut
from app.services.audit_service import log_action
from app.utils.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse

router = APIRouter(prefix="/connections", tags=["Service Connections"])


@router.post("", response_model=ConnectionOut, status_code=201)
def create_connection(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    customer = CustomerRepository(db).get(payload.customer_id)
    if customer is None:
        raise NotFoundException("Customer not found.")

    repo = ConnectionRepository(db)
    if repo.get_by_connection_number(payload.connection_number):
        raise ConflictException(f"Connection number '{payload.connection_number}' already exists.")

    connection = repo.create(payload.model_dump())
    log_action(db, current_user.id, "CREATE", "Connection", connection.id)
    return connection


@router.get("", response_model=PaginatedResponse[ConnectionOut])
def list_connections(
    connection_type: str | None = None,
    tariff_type: str | None = None,
    status: str | None = None,
    customer_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ConnectionRepository(db)
    query = repo.filtered_query(connection_type, tariff_type, status, customer_id)
    query = apply_sorting(query, Connection, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/{connection_id}", response_model=ConnectionOut)
def get_connection(connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    connection = ConnectionRepository(db).get(connection_id)
    if connection is None:
        raise NotFoundException("Connection not found.")
    return connection


@router.put("/{connection_id}", response_model=ConnectionOut)
def update_connection(
    connection_id: int,
    payload: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = ConnectionRepository(db)
    connection = repo.get(connection_id)
    if connection is None:
        raise NotFoundException("Connection not found.")
    connection = repo.update(connection, payload.model_dump(exclude_unset=True))
    log_action(db, current_user.id, "UPDATE", "Connection", connection.id)
    return connection


@router.post("/{connection_id}/disconnect", response_model=ConnectionOut)
def disconnect_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    repo = ConnectionRepository(db)
    connection = repo.get(connection_id)
    if connection is None:
        raise NotFoundException("Connection not found.")
    if connection.status == ConnectionStatus.DISCONNECTED:
        raise BadRequestException("Connection is already disconnected.")

    connection.status = ConnectionStatus.DISCONNECTED
    db.commit()
    db.refresh(connection)
    log_action(db, current_user.id, "UPDATE", "Connection", connection.id, "Disconnected")
    return connection
