from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.models.connection import ConnectionType, ConnectionStatus


class ConnectionCreate(BaseModel):
    customer_id: int
    connection_number: str = Field(min_length=1, max_length=50)
    connection_type: ConnectionType
    sanctioned_load: Decimal = Field(gt=0)
    tariff_type: str = Field(min_length=1, max_length=50)
    connection_date: date
    status: ConnectionStatus = ConnectionStatus.ACTIVE


class ConnectionUpdate(BaseModel):
    connection_type: ConnectionType | None = None
    sanctioned_load: Decimal | None = None
    tariff_type: str | None = None
    status: ConnectionStatus | None = None


class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    connection_number: str
    connection_type: ConnectionType
    sanctioned_load: Decimal
    tariff_type: str
    connection_date: date
    status: ConnectionStatus
    created_at: datetime
