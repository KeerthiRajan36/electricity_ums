import enum

from sqlalchemy import (
    Column, Integer, String, DateTime, Enum as SAEnum, Boolean, ForeignKey, Numeric, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ConnectionType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"


class ConnectionStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    SUSPENDED = "suspended"


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    connection_number = Column(String(50), unique=True, index=True, nullable=False)
    connection_type = Column(SAEnum(ConnectionType), nullable=False, index=True)
    sanctioned_load = Column(Numeric(10, 2), nullable=False)  # in kW
    tariff_type = Column(String(50), nullable=False)
    connection_date = Column(Date, nullable=False)
    status = Column(SAEnum(ConnectionStatus), nullable=False, default=ConnectionStatus.ACTIVE, index=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="connections")
    meters = relationship("Meter", back_populates="connection")
    bills = relationship("Bill", back_populates="connection")
    complaints = relationship("Complaint", back_populates="connection")
    service_requests = relationship("ServiceRequest", back_populates="connection")
