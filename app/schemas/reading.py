from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.reading import ReadingSource


class MeterReadingCreate(BaseModel):
    meter_id: int
    reading_date: date
    current_reading: Decimal = Field(ge=0)
    reading_source: ReadingSource = ReadingSource.MANUAL
    remarks: str | None = None
    # billing_period defaults to the reading_date's "YYYY-MM" if not supplied
    billing_period: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")

    @model_validator(mode="after")
    def default_billing_period(self):
        if not self.billing_period:
            self.billing_period = self.reading_date.strftime("%Y-%m")
        return self


class MeterReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meter_id: int
    reading_date: date
    previous_reading: Decimal
    current_reading: Decimal
    units_consumed: Decimal
    reading_source: ReadingSource
    billing_period: str
    remarks: str | None = None
