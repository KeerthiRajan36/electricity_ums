from sqlalchemy.orm import Session

from app.models.meter import Meter, MeterStatus
from app.repositories.base import BaseRepository


class MeterRepository(BaseRepository[Meter]):
    def __init__(self, db: Session):
        super().__init__(Meter, db)

    def get_by_meter_number(self, meter_number: str) -> Meter | None:
        return self.base_query().filter(Meter.meter_number == meter_number).first()

    def get_active_for_connection(self, connection_id: int) -> Meter | None:
        return self.base_query().filter(
            Meter.connection_id == connection_id, Meter.meter_status == MeterStatus.ACTIVE
        ).first()
