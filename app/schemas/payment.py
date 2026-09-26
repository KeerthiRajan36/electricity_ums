from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    transaction_id: str = Field(min_length=1, max_length=100)
    # Lets the mock gateway simulate a failed payment for testing purposes.
    simulate_status: PaymentStatus | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bill_id: int
    amount: Decimal
    payment_method: PaymentMethod
    transaction_id: str
    payment_date: datetime
    payment_status: PaymentStatus
