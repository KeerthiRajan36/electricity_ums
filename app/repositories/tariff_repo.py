from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.tariff import Tariff, TariffStatus
from app.repositories.base import BaseRepository


class TariffRepository(BaseRepository[Tariff]):
    def __init__(self, db: Session):
        super().__init__(Tariff, db)

    def get_slabs(self, connection_type: str, as_of: date) -> list[Tariff]:
        """Return all applicable slab rows for a connection type on a given date,
        ordered by minimum_units ascending."""
        return (
            self.base_query()
            .filter(
                Tariff.connection_type == connection_type,
                Tariff.status == TariffStatus.ACTIVE,
                Tariff.effective_from <= as_of,
                or_(Tariff.effective_to.is_(None), Tariff.effective_to >= as_of),
            )
            .order_by(Tariff.minimum_units.asc())
            .all()
        )
