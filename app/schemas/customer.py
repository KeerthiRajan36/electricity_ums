from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.customer import CustomerStatus


class CustomerCreate(BaseModel):
    customer_number: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    address: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    status: CustomerStatus | None = None


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_number: str
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime | None = None
