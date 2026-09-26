from sqlalchemy.orm import Session, Query, joinedload

from app.models.connection import Connection
from app.repositories.base import BaseRepository


class ConnectionRepository(BaseRepository[Connection]):
    def __init__(self, db: Session):
        super().__init__(Connection, db)

    def get_by_connection_number(self, connection_number: str) -> Connection | None:
        return self.base_query().filter(Connection.connection_number == connection_number).first()

    def get_with_customer(self, id_: int) -> Connection | None:
        return (
            self.base_query()
            .options(joinedload(Connection.customer))
            .filter(Connection.id == id_)
            .first()
        )

    def filtered_query(
        self,
        connection_type: str | None,
        tariff_type: str | None,
        status: str | None,
        customer_id: int | None = None,
    ) -> Query:
        query = self.base_query()
        if connection_type:
            query = query.filter(Connection.connection_type == connection_type)
        if tariff_type:
            query = query.filter(Connection.tariff_type == tariff_type)
        if status:
            query = query.filter(Connection.status == status)
        if customer_id:
            query = query.filter(Connection.customer_id == customer_id)
        return query

    def count_active_for_customer(self, customer_id: int) -> int:
        return self.base_query().filter(
            Connection.customer_id == customer_id, Connection.status == "active"
        ).count()
