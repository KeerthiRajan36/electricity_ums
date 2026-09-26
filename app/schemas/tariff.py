from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.models.connection import ConnectionType
from app.models.tariff import TariffStatus


class TariffCreate(BaseModel):
    tariff_name: str = Field(min_length=1, max_length=100)
    connection_type: ConnectionType
    minimum_units: Decimal = Field(ge=0)
    maximum_units: Decimal | None = None
    rate_per_unit: Decimal = Field(gt=0)
    fixed_charge: Decimal = Field(ge=0, default=0)
    effective_from: date
    effective_to: date | None = None
    status: TariffStatus = TariffStatus.ACTIVE


class TariffUpdate(BaseModel):
    rate_per_unit: Decimal | None = None
    fixed_charge: Decimal | None = None
    maximum_units: Decimal | None = None
    effective_to: date | None = None
    status: TariffStatus | None = None


class TariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tariff_name: str
    connection_type: ConnectionType
    minimum_units: Decimal
    maximum_units: Decimal | None
    rate_per_unit: Decimal
    fixed_charge: Decimal
    effective_from: date
    effective_to: date | None
    status: TariffStatus
