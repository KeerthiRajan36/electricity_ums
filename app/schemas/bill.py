from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.models.bill import BillStatus


class BillGenerateRequest(BaseModel):
    connection_id: int
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    discount: Decimal = Field(ge=0, default=0)


class BillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connection_id: int
    billing_month: str
    units_consumed: Decimal
    energy_charge: Decimal
    fixed_charge: Decimal
    tax: Decimal
    late_fee: Decimal
    discount: Decimal
    total_amount: Decimal
    due_date: date
    bill_status: BillStatus
