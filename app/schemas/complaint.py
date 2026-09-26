from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.complaint import ComplaintType, ComplaintPriority, ComplaintStatus


class ComplaintCreate(BaseModel):
    customer_id: int
    connection_id: int | None = None
    complaint_type: ComplaintType
    description: str = Field(min_length=5)
    priority: ComplaintPriority = ComplaintPriority.MEDIUM


class ComplaintAssignRequest(BaseModel):
    technician_id: int


class ComplaintStatusUpdateRequest(BaseModel):
    status: ComplaintStatus


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    connection_id: int | None
    complaint_type: ComplaintType
    description: str
    priority: ComplaintPriority
    assigned_to: int | None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime | None = None


class ComplaintHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event: str
    actor_user_id: int | None
    created_at: datetime
