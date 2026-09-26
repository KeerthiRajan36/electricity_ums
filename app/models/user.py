import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    BILLING_OFFICER = "billing_officer"
    FIELD_TECHNICIAN = "field_technician"
    CUSTOMER_SERVICE_AGENT = "customer_service_agent"
    CUSTOMER = "customer"


# Roles allowed to be self-assigned at public registration. Staff roles must
# be created by a Super Admin via the (role-protected) registration flow.
SELF_REGISTERABLE_ROLES = {UserRole.CUSTOMER}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.CUSTOMER, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Optional link from a CUSTOMER-role user to their customer record.
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="user_account", foreign_keys=[customer_id])
