import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, Numeric, Date, Boolean
from sqlalchemy.sql import func

from app.database import Base
from app.models.connection import ConnectionType


class TariffStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Tariff(Base):
    """
    A tariff represents a single pricing slab for a connection type.
    Slab-based pricing is modelled by creating multiple Tariff rows with the
    same tariff_name/connection_type but different (minimum_units, maximum_units)
    ranges, e.g.:
        ("Domestic", 0, 100, 3.50)
        ("Domestic", 101, 200, 4.50)
        ("Domestic", 201, 500, 6.00)
        ("Domestic", 501, None, 8.00)
    """
    __tablename__ = "tariffs"

    id = Column(Integer, primary_key=True, index=True)
    tariff_name = Column(String(100), nullable=False, index=True)
    connection_type = Column(SAEnum(ConnectionType), nullable=False, index=True)
    minimum_units = Column(Numeric(12, 2), nullable=False)
    maximum_units = Column(Numeric(12, 2), nullable=True)  # NULL = unbounded (500+ units)
    rate_per_unit = Column(Numeric(10, 4), nullable=False)
    fixed_charge = Column(Numeric(10, 2), nullable=False, default=0)
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True)
    status = Column(SAEnum(TariffStatus), nullable=False, default=TariffStatus.ACTIVE, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
