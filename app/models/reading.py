import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReadingSource(str, enum.Enum):
    MANUAL = "manual"
    SMART_METER = "smart_meter"
    FIELD_TECHNICIAN = "field_technician"


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=False, index=True)
    reading_date = Column(Date, nullable=False, index=True)
    previous_reading = Column(Numeric(12, 2), nullable=False)
    current_reading = Column(Numeric(12, 2), nullable=False)
    units_consumed = Column(Numeric(12, 2), nullable=False)
    reading_source = Column(SAEnum(ReadingSource), nullable=False, default=ReadingSource.MANUAL)
    remarks = Column(String(255), nullable=True)

    # Billing period this reading belongs to, e.g. "2026-09". Used to prevent
    # duplicate readings for the same meter + billing period.
    billing_period = Column(String(7), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meter = relationship("Meter", back_populates="readings")
