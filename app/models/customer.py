import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    status = Column(SAEnum(CustomerStatus), nullable=False, default=CustomerStatus.ACTIVE, index=True)

    is_deleted = Column(Boolean, default=False, nullable=False)  # soft delete
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connections = relationship("Connection", back_populates="customer")
    complaints = relationship("Complaint", back_populates="customer")
    service_requests = relationship("ServiceRequest", back_populates="customer")
    user_account = relationship("User", back_populates="customer", uselist=False, foreign_keys="User.customer_id")
