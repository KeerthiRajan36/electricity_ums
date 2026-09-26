from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    """Records who did what to which entity, for security/traceability (Level 16)."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # CREATE / UPDATE / DELETE / LOGIN ...
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Notification(Base):
    """
    In-app record of a notification that was (or would be) sent out.
    A real deployment would push these through email/SMS/push providers;
    here they are persisted so they can be inspected/tested (Level 15).
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
