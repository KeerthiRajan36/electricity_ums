from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_transaction_id(self, transaction_id: str) -> Payment | None:
        return self.base_query().filter(Payment.transaction_id == transaction_id).first()

    def get_for_bill(self, bill_id: int):
        return self.base_query().filter(Payment.bill_id == bill_id).all()

    def total_successful_for_bill(self, bill_id: int):
        from sqlalchemy import func
        from app.models.payment import PaymentStatus

        total = (
            self.db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.bill_id == bill_id, Payment.payment_status == PaymentStatus.SUCCESS)
            .scalar()
        )
        return total
