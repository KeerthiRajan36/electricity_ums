import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MeterType(str, enum.Enum):
    ANALOG = "analog"
    DIGITAL = "digital"
    SMART = "smart"


class MeterStatus(str, enum.Enum):
    ACTIVE = "active"
    FAULTY = "faulty"
    REMOVED = "removed"


class Meter(Base):
    __tablename__ = "meters"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)
    meter_number = Column(String(50), unique=True, index=True, nullable=False)
    meter_type = Column(SAEnum(MeterType), nullable=False, default=MeterType.SMART)
    installation_date = Column(Date, nullable=False)
    initial_reading = Column(Numeric(12, 2), nullable=False, default=0)
    current_reading = Column(Numeric(12, 2), nullable=False, default=0)
    meter_status = Column(SAEnum(MeterStatus), nullable=False, default=MeterStatus.ACTIVE, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connection = relationship("Connection", back_populates="meters")
    readings = relationship("MeterReading", back_populates="meter")
