from sqlalchemy.orm import Session

from app.models.service_request import ServiceRequest
from app.repositories.base import BaseRepository


class ServiceRequestRepository(BaseRepository[ServiceRequest]):
    def __init__(self, db: Session):
        super().__init__(ServiceRequest, db)
