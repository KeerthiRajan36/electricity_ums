from sqlalchemy.orm import Session, Query

from app.models.complaint import Complaint
from app.repositories.base import BaseRepository


class ComplaintRepository(BaseRepository[Complaint]):
    def __init__(self, db: Session):
        super().__init__(Complaint, db)

    def filtered_query(
        self,
        priority: str | None,
        status: str | None,
        complaint_type: str | None,
        assigned_to: int | None,
    ) -> Query:
        query = self.base_query()
        if priority:
            query = query.filter(Complaint.priority == priority)
        if status:
            query = query.filter(Complaint.status == status)
        if complaint_type:
            query = query.filter(Complaint.complaint_type == complaint_type)
        if assigned_to:
            query = query.filter(Complaint.assigned_to == assigned_to)
        return query
