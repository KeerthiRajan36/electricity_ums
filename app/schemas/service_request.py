from datetime import date

from pydantic import BaseModel, Field, ConfigDict

from app.models.service_request import ServiceRequestType, ServiceRequestStatus


class ServiceRequestCreate(BaseModel):
    customer_id: int
    connection_id: int | None = None
    request_type: ServiceRequestType
    description: str = Field(min_length=5)
    requested_date: date


class ServiceRequestRejectRequest(BaseModel):
    reason: str = Field(min_length=3)


class ServiceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    connection_id: int | None
    request_type: ServiceRequestType
    description: str
    requested_date: date
    status: ServiceRequestStatus
