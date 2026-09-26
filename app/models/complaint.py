import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ComplaintType(str, enum.Enum):
    POWER_FAILURE = "power_failure"
    VOLTAGE_ISSUE = "voltage_issue"
    METER_ISSUE = "meter_issue"
    BILLING_ISSUE = "billing_issue"
    CONNECTION_ISSUE = "connection_issue"
    OTHER = "other"


class ComplaintPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=True, index=True)
    complaint_type = Column(SAEnum(ComplaintType), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(SAEnum(ComplaintPriority), nullable=False, default=ComplaintPriority.MEDIUM, index=True)
    assigned_to = Column(Integer, ForeignKey("technicians.id"), nullable=True, index=True)
    status = Column(SAEnum(ComplaintStatus), nullable=False, default=ComplaintStatus.OPEN, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="complaints")
    connection = relationship("Connection", back_populates="complaints")
    technician = relationship("Technician", back_populates="complaints")
    history = relationship("ComplaintHistory", back_populates="complaint", order_by="ComplaintHistory.created_at")


class ComplaintHistory(Base):
    """Append-only audit trail of every status/assignment change on a complaint."""
    __tablename__ = "complaint_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    event = Column(String(255), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    complaint = relationship("Complaint", back_populates="history")
