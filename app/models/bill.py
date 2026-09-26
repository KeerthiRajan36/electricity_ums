import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class BillStatus(str, enum.Enum):
    GENERATED = "generated"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)
    billing_month = Column(String(7), nullable=False, index=True)  # "YYYY-MM"
    units_consumed = Column(Numeric(12, 2), nullable=False)
    energy_charge = Column(Numeric(12, 2), nullable=False)
    fixed_charge = Column(Numeric(12, 2), nullable=False, default=0)
    tax = Column(Numeric(12, 2), nullable=False, default=0)
    late_fee = Column(Numeric(12, 2), nullable=False, default=0)
    discount = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    bill_status = Column(SAEnum(BillStatus), nullable=False, default=BillStatus.GENERATED, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connection = relationship("Connection", back_populates="bills")
    payments = relationship("Payment", back_populates="bill")
