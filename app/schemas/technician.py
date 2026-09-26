from pydantic import BaseModel, Field, ConfigDict

from app.models.technician import AvailabilityStatus


class TechnicianCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    employee_id: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=7, max_length=20)
    specialization: str = Field(min_length=1, max_length=100)


class TechnicianAvailabilityUpdate(BaseModel):
    availability_status: AvailabilityStatus


class TechnicianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    employee_id: str
    phone: str
    specialization: str
    availability_status: AvailabilityStatus
