import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFF_DUTY = "off_duty"


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    specialization = Column(String(100), nullable=False)
    availability_status = Column(
        SAEnum(AvailabilityStatus), nullable=False, default=AvailabilityStatus.AVAILABLE, index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    complaints = relationship("Complaint", back_populates="technician")
