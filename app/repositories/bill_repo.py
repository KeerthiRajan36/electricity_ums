from decimal import Decimal

from sqlalchemy.orm import Session, Query

from app.models.bill import Bill
from app.models.connection import Connection
from app.repositories.base import BaseRepository


class BillRepository(BaseRepository[Bill]):
    def __init__(self, db: Session):
        super().__init__(Bill, db)

    def get_for_connection_and_month(self, connection_id: int, billing_month: str) -> Bill | None:
        return self.base_query().filter(
            Bill.connection_id == connection_id, Bill.billing_month == billing_month
        ).first()

    def get_for_connection(self, connection_id: int):
        return self.base_query().filter(Bill.connection_id == connection_id).order_by(
            Bill.billing_month
        ).all()

    def get_for_customer(self, customer_id: int):
        return (
            self.db.query(Bill)
            .join(Connection, Connection.id == Bill.connection_id)
            .filter(Connection.customer_id == customer_id)
            .order_by(Bill.billing_month)
            .all()
        )

    def filtered_query(
        self,
        billing_month: str | None,
        bill_status: str | None,
        min_amount: Decimal | None,
        max_amount: Decimal | None,
    ) -> Query:
        query = self.base_query()
        if billing_month:
            query = query.filter(Bill.billing_month == billing_month)
        if bill_status:
            query = query.filter(Bill.bill_status == bill_status)
        if min_amount is not None:
            query = query.filter(Bill.total_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Bill.total_amount <= max_amount)
        return query
