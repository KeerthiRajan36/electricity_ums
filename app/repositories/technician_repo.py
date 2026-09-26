from sqlalchemy.orm import Session

from app.models.technician import Technician, AvailabilityStatus
from app.repositories.base import BaseRepository


class TechnicianRepository(BaseRepository[Technician]):
    def __init__(self, db: Session):
        super().__init__(Technician, db)

    def get_by_employee_id(self, employee_id: str) -> Technician | None:
        return self.base_query().filter(Technician.employee_id == employee_id).first()

    def get_available(self):
        return self.base_query().filter(
            Technician.availability_status == AvailabilityStatus.AVAILABLE
        ).all()
