import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    CARD = "card"
    NET_BANKING = "net_banking"
    WALLET = "wallet"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=False)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_status = Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)

    bill = relationship("Bill", back_populates="payments")
