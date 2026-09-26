from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.connection_repo import ConnectionRepository
from app.repositories.customer_repo import CustomerRepository
from app.services import analytics_service
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/analytics", tags=["Consumption Analytics"])


@router.get("/connections/{connection_id}/monthly")
def monthly_consumption(
    connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if ConnectionRepository(db).get(connection_id) is None:
        raise NotFoundException("Connection not found.")
    return analytics_service.monthly_consumption_for_connection(db, connection_id)


@router.get("/connections/{connection_id}/yearly")
def yearly_consumption(
    connection_id: int,
    year: str = Query(default_factory=lambda: str(date.today().year), pattern=r"^\d{4}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if ConnectionRepository(db).get(connection_id) is None:
        raise NotFoundException("Connection not found.")
    return analytics_service.yearly_consumption_for_connection(db, connection_id, year)


@router.get("/connections/{connection_id}/usage")
def connection_wise_usage(
    connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return analytics_service.connection_wise_usage(db, connection_id)


@router.get("/customers/{customer_id}/usage")
def customer_wise_usage(
    customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if CustomerRepository(db).get(customer_id) is None:
        raise NotFoundException("Customer not found.")
    return analytics_service.customer_wise_usage(db, customer_id)


@router.get("/connections/highest-consuming")
def highest_consuming_connections(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.highest_consuming_connections(db, limit)


@router.get("/connections/{connection_id}/average-monthly")
def average_monthly_consumption(
    connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if ConnectionRepository(db).get(connection_id) is None:
        raise NotFoundException("Connection not found.")
    return analytics_service.average_monthly_consumption(db, connection_id)
