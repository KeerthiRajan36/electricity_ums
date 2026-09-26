"""
Level 15 - Notifications & Background Tasks.

In a production system these would call an email/SMS/push provider (and the
README's bonus section shows how to swap in Celery + Redis for durable async
delivery). Here, `send_notification` is the function handed to FastAPI's
BackgroundTasks: it runs after the HTTP response has already gone out, logs
the event, and persists a Notification row so the effect is inspectable
and testable.
"""
import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.audit import Notification

logger = logging.getLogger("notifications")


def send_notification(customer_id: int | None, event_type: str, message: str) -> None:
    # BackgroundTasks run outside the request's DB session lifecycle, so we
    # open a short-lived session here.
    db: Session = SessionLocal()
    try:
        logger.info("[NOTIFICATION] event=%s customer_id=%s message=%s", event_type, customer_id, message)
        notification = Notification(recipient_customer_id=customer_id, event_type=event_type, message=message)
        db.add(notification)
        db.commit()
    finally:
        db.close()


# Convenience builders for each event type listed in the spec ---------------

def bill_generated(customer_id: int, bill_id: int, amount) -> tuple[int, str, str]:
    return customer_id, "bill_generated", f"Bill #{bill_id} generated for amount {amount}."


def bill_due_reminder(customer_id: int, bill_id: int, due_date) -> tuple[int, str, str]:
    return customer_id, "bill_due_reminder", f"Bill #{bill_id} is due on {due_date}."


def bill_overdue(customer_id: int, bill_id: int) -> tuple[int, str, str]:
    return customer_id, "bill_overdue", f"Bill #{bill_id} is now overdue."


def payment_success(customer_id: int, bill_id: int, amount) -> tuple[int, str, str]:
    return customer_id, "payment_success", f"Payment of {amount} received for bill #{bill_id}."


def payment_failure(customer_id: int, bill_id: int, amount) -> tuple[int, str, str]:
    return customer_id, "payment_failure", f"Payment of {amount} failed for bill #{bill_id}."


def complaint_assigned(customer_id: int, complaint_id: int, technician_name: str) -> tuple[int, str, str]:
    return customer_id, "complaint_assigned", f"Complaint #{complaint_id} assigned to {technician_name}."


def complaint_resolved(customer_id: int, complaint_id: int) -> tuple[int, str, str]:
    return customer_id, "complaint_resolved", f"Complaint #{complaint_id} has been resolved."


def service_request_approved(customer_id: int, request_id: int) -> tuple[int, str, str]:
    return customer_id, "service_request_approved", f"Service request #{request_id} was approved."


def meter_replacement_completed(customer_id: int, meter_number: str) -> tuple[int, str, str]:
    return customer_id, "meter_replacement_completed", f"Meter replaced. New meter number: {meter_number}."
