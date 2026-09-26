import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ServiceRequestType(str, enum.Enum):
    NEW_CONNECTION = "new_connection"
    LOAD_CHANGE = "load_change"
    METER_REPLACEMENT = "meter_replacement"
    NAME_CHANGE = "name_change"
    ADDRESS_CHANGE = "address_change"
    DISCONNECTION = "disconnection"
    RECONNECTION = "reconnection"


class ServiceRequestStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=True, index=True)
    request_type = Column(SAEnum(ServiceRequestType), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requested_date = Column(Date, nullable=False)
    status = Column(SAEnum(ServiceRequestStatus), nullable=False, default=ServiceRequestStatus.SUBMITTED, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="service_requests")
    connection = relationship("Connection", back_populates="service_requests")
