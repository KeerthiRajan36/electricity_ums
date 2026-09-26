from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.models.meter import MeterType, MeterStatus


class MeterCreate(BaseModel):
    connection_id: int
    meter_number: str = Field(min_length=1, max_length=50)
    meter_type: MeterType = MeterType.SMART
    installation_date: date
    initial_reading: Decimal = Field(ge=0, default=0)


class MeterUpdate(BaseModel):
    meter_type: MeterType | None = None
    meter_status: MeterStatus | None = None


class MeterReplaceRequest(BaseModel):
    new_meter_number: str = Field(min_length=1, max_length=50)
    new_meter_type: MeterType = MeterType.SMART
    installation_date: date
    initial_reading: Decimal = Field(ge=0, default=0)
    technician_id: int | None = None


class MeterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connection_id: int
    meter_number: str
    meter_type: MeterType
    installation_date: date
    initial_reading: Decimal
    current_reading: Decimal
    meter_status: MeterStatus
    created_at: datetime
