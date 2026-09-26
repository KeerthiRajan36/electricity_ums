from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.connection import Connection
from app.utils.exceptions import NotFoundException


def monthly_consumption_for_connection(db: Session, connection_id: int) -> list[dict]:
    rows = (
        db.query(Bill.billing_month, Bill.units_consumed, Bill.total_amount)
        .filter(Bill.connection_id == connection_id)
        .order_by(Bill.billing_month)
        .all()
    )
    return [
        {"month": month, "units_consumed": units, "bill_amount": amount}
        for month, units, amount in rows
    ]


def yearly_consumption_for_connection(db: Session, connection_id: int, year: str) -> dict:
    result = (
        db.query(
            func.coalesce(func.sum(Bill.units_consumed), 0),
            func.coalesce(func.sum(Bill.total_amount), 0),
            func.count(Bill.id),
        )
        .filter(Bill.connection_id == connection_id, Bill.billing_month.like(f"{year}-%"))
        .first()
    )
    total_units, total_amount, bill_count = result
    return {
        "connection_id": connection_id,
        "year": year,
        "total_units_consumed": total_units,
        "total_bill_amount": total_amount,
        "bills_count": bill_count,
    }


def connection_wise_usage(db: Session, connection_id: int) -> dict:
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if connection is None:
        raise NotFoundException("Connection not found.")

    total_units, total_amount, bill_count = (
        db.query(
            func.coalesce(func.sum(Bill.units_consumed), 0),
            func.coalesce(func.sum(Bill.total_amount), 0),
            func.count(Bill.id),
        )
        .filter(Bill.connection_id == connection_id)
        .first()
    )
    avg_units = (Decimal(total_units) / bill_count) if bill_count else Decimal("0")
    return {
        "connection_id": connection_id,
        "connection_number": connection.connection_number,
        "total_units_consumed": total_units,
        "total_bill_amount": total_amount,
        "bills_count": bill_count,
        "average_monthly_units": avg_units.quantize(Decimal("0.01")),
    }


def customer_wise_usage(db: Session, customer_id: int) -> dict:
    total_units, total_amount, bill_count = (
        db.query(
            func.coalesce(func.sum(Bill.units_consumed), 0),
            func.coalesce(func.sum(Bill.total_amount), 0),
            func.count(Bill.id),
        )
        .join(Connection, Connection.id == Bill.connection_id)
        .filter(Connection.customer_id == customer_id)
        .first()
    )
    return {
        "customer_id": customer_id,
        "total_units_consumed": total_units,
        "total_bill_amount": total_amount,
        "bills_count": bill_count,
    }


def highest_consuming_connections(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(
            Bill.connection_id,
            Connection.connection_number,
            func.sum(Bill.units_consumed).label("total_units"),
        )
        .join(Connection, Connection.id == Bill.connection_id)
        .group_by(Bill.connection_id, Connection.connection_number)
        .order_by(func.sum(Bill.units_consumed).desc())
        .limit(limit)
        .all()
    )
    return [
        {"connection_id": cid, "connection_number": cnum, "total_units_consumed": total}
        for cid, cnum, total in rows
    ]


def average_monthly_consumption(db: Session, connection_id: int) -> dict:
    total_units, bill_count = (
        db.query(func.coalesce(func.sum(Bill.units_consumed), 0), func.count(Bill.id))
        .filter(Bill.connection_id == connection_id)
        .first()
    )
    average = (Decimal(total_units) / bill_count) if bill_count else Decimal("0")
    return {
        "connection_id": connection_id,
        "average_monthly_units": average.quantize(Decimal("0.01")),
        "months_counted": bill_count,
    }
