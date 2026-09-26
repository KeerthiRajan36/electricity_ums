from sqlalchemy.orm import Session

from app.models.reading import MeterReading
from app.repositories.base import BaseRepository


class ReadingRepository(BaseRepository[MeterReading]):
    def __init__(self, db: Session):
        super().__init__(MeterReading, db)

    def get_for_meter(self, meter_id: int):
        return self.base_query().filter(MeterReading.meter_id == meter_id).order_by(
            MeterReading.reading_date
        ).all()

    def get_for_connection(self, connection_id: int):
        from app.models.meter import Meter

        return (
            self.db.query(MeterReading)
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(Meter.connection_id == connection_id)
            .order_by(MeterReading.reading_date)
            .all()
        )

    def exists_for_period(self, meter_id: int, billing_period: str) -> bool:
        return (
            self.base_query()
            .filter(MeterReading.meter_id == meter_id, MeterReading.billing_period == billing_period)
            .first()
            is not None
        )

    def get_latest_for_meter(self, meter_id: int) -> MeterReading | None:
        return (
            self.base_query()
            .filter(MeterReading.meter_id == meter_id)
            .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
            .first()
        )
