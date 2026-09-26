from datetime import date

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.connection import Connection, ConnectionStatus
from app.models.meter import Meter, MeterStatus
from app.models.bill import Bill, BillStatus
from app.models.payment import Payment, PaymentStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.technician import Technician
from app.models.service_request import ServiceRequest


def admin_dashboard_summary(db: Session, month: str | None = None) -> dict:
    month = month or date.today().strftime("%Y-%m")

    total_customers = db.query(func.count(Customer.id)).filter(Customer.is_deleted.is_(False)).scalar()
    active_connections = db.query(func.count(Connection.id)).filter(
        Connection.status == ConnectionStatus.ACTIVE, Connection.is_deleted.is_(False)
    ).scalar()
    disconnected_connections = db.query(func.count(Connection.id)).filter(
        Connection.status == ConnectionStatus.DISCONNECTED, Connection.is_deleted.is_(False)
    ).scalar()
    total_meters = db.query(func.count(Meter.id)).scalar()
    faulty_meters = db.query(func.count(Meter.id)).filter(Meter.meter_status == MeterStatus.FAULTY).scalar()

    monthly_units, monthly_revenue = (
        db.query(func.coalesce(func.sum(Bill.units_consumed), 0), func.coalesce(func.sum(Bill.total_amount), 0))
        .filter(Bill.billing_month == month)
        .first()
    )
    pending_bills = db.query(func.count(Bill.id)).filter(
        Bill.bill_status.in_([BillStatus.GENERATED, BillStatus.PENDING])
    ).scalar()
    overdue_bills = db.query(func.count(Bill.id)).filter(Bill.bill_status == BillStatus.OVERDUE).scalar()

    open_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status.in_([ComplaintStatus.OPEN, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS])
    ).scalar()
    resolved_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
    ).scalar()

    return {
        "month": month,
        "total_customers": total_customers,
        "active_connections": active_connections,
        "disconnected_connections": disconnected_connections,
        "total_meters": total_meters,
        "faulty_meters": faulty_meters,
        "monthly_units_consumed": monthly_units,
        "monthly_revenue": monthly_revenue,
        "pending_bills": pending_bills,
        "overdue_bills": overdue_bills,
        "open_complaints": open_complaints,
        "resolved_complaints": resolved_complaints,
    }


def daily_collection_report(db: Session, day: date) -> dict:
    total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(func.date(Payment.payment_date) == day, Payment.payment_status == PaymentStatus.SUCCESS)
        .scalar()
    )
    count = (
        db.query(func.count(Payment.id))
        .filter(func.date(Payment.payment_date) == day, Payment.payment_status == PaymentStatus.SUCCESS)
        .scalar()
    )
    return {"date": day.isoformat(), "total_collected": total, "payments_count": count}


def monthly_revenue_report(db: Session, month: str) -> dict:
    total_billed = db.query(func.coalesce(func.sum(Bill.total_amount), 0)).filter(
        Bill.billing_month == month
    ).scalar()
    total_collected = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .join(Bill, Bill.id == Payment.bill_id)
        .filter(Bill.billing_month == month, Payment.payment_status == PaymentStatus.SUCCESS)
        .scalar()
    )
    return {"month": month, "total_billed": total_billed, "total_collected": total_collected}


def customer_wise_billing_report(db: Session, customer_id: int) -> list[dict]:
    rows = (
        db.query(Bill.billing_month, Bill.total_amount, Bill.bill_status)
        .join(Connection, Connection.id == Bill.connection_id)
        .filter(Connection.customer_id == customer_id)
        .order_by(Bill.billing_month)
        .all()
    )
    return [{"billing_month": m, "total_amount": a, "status": s.value} for m, a, s in rows]


def connection_wise_consumption_report(db: Session) -> list[dict]:
    rows = (
        db.query(
            Bill.connection_id,
            Connection.connection_number,
            func.sum(Bill.units_consumed).label("total_units"),
            func.sum(Bill.total_amount).label("total_amount"),
        )
        .join(Connection, Connection.id == Bill.connection_id)
        .group_by(Bill.connection_id, Connection.connection_number)
        .all()
    )
    return [
        {
            "connection_id": cid,
            "connection_number": cnum,
            "total_units_consumed": units,
            "total_amount": amount,
        }
        for cid, cnum, units, amount in rows
    ]


def technician_performance_report(db: Session) -> list[dict]:
    rows = (
        db.query(
            Technician.id,
            Technician.name,
            func.count(Complaint.id).label("total_assigned"),
            func.sum(
                case((Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]), 1), else_=0)
            ).label("resolved_count"),
        )
        .outerjoin(Complaint, Complaint.assigned_to == Technician.id)
        .group_by(Technician.id, Technician.name)
        .all()
    )
    return [
        {
            "technician_id": tid,
            "name": name,
            "total_assigned": total or 0,
            "resolved_count": resolved or 0,
        }
        for tid, name, total, resolved in rows
    ]


def complaint_resolution_report(db: Session) -> dict:
    by_status = dict(
        db.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
    )
    by_priority = dict(
        db.query(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority).all()
    )
    return {
        "by_status": {status.value: count for status, count in by_status.items()},
        "by_priority": {priority.value: count for priority, count in by_priority.items()},
    }


def outstanding_payment_report(db: Session) -> list[dict]:
    rows = (
        db.query(Bill.id, Bill.connection_id, Bill.billing_month, Bill.total_amount, Bill.due_date)
        .filter(Bill.bill_status.in_([BillStatus.GENERATED, BillStatus.PENDING, BillStatus.OVERDUE]))
        .order_by(Bill.due_date)
        .all()
    )
    return [
        {
            "bill_id": bid,
            "connection_id": cid,
            "billing_month": month,
            "amount_due": amount,
            "due_date": due.isoformat(),
        }
        for bid, cid, month, amount, due in rows
    ]
