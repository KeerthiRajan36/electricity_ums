from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_staff, require_admin_or_billing, get_current_user
from app.models.customer import Customer
from app.models.user import User
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut
from app.services.audit_service import log_action
from app.utils.exceptions import NotFoundException, ConflictException
from app.utils.pagination import apply_sorting, paginate, build_paginated_response, PaginatedResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = CustomerRepository(db)
    if repo.get_by_customer_number(payload.customer_number):
        raise ConflictException(f"Customer number '{payload.customer_number}' already exists.")
    if repo.get_by_email(payload.email):
        raise ConflictException(f"Email '{payload.email}' already exists.")

    customer = repo.create(payload.model_dump())
    log_action(db, current_user.id, "CREATE", "Customer", customer.id)
    return customer


@router.get("", response_model=PaginatedResponse[CustomerOut])
def list_customers(
    city: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str | None = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = CustomerRepository(db)
    query = repo.filtered_query(city, status)
    query = apply_sorting(query, Customer, sort_by, sort_order)
    items, total = paginate(query, page, limit)
    return build_paginated_response(items, total, page, limit)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer = CustomerRepository(db).get(customer_id)
    if customer is None:
        raise NotFoundException("Customer not found.")
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    repo = CustomerRepository(db)
    customer = repo.get(customer_id)
    if customer is None:
        raise NotFoundException("Customer not found.")
    if payload.email and payload.email != customer.email and repo.get_by_email(payload.email):
        raise ConflictException(f"Email '{payload.email}' already exists.")

    customer = repo.update(customer, payload.model_dump(exclude_unset=True))
    log_action(db, current_user.id, "UPDATE", "Customer", customer.id)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    repo = CustomerRepository(db)
    customer = repo.get(customer_id)
    if customer is None:
        raise NotFoundException("Customer not found.")
    repo.delete(customer, soft=True)
    log_action(db, current_user.id, "DELETE", "Customer", customer_id)
    return None
