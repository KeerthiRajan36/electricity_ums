from sqlalchemy.orm import Session, Query

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session):
        super().__init__(Customer, db)

    def get_by_customer_number(self, customer_number: str) -> Customer | None:
        return self.base_query().filter(Customer.customer_number == customer_number).first()

    def get_by_email(self, email: str) -> Customer | None:
        return self.base_query().filter(Customer.email == email).first()

    def filtered_query(self, city: str | None, status: str | None) -> Query:
        query = self.base_query()
        if city:
            query = query.filter(Customer.city.ilike(f"%{city}%"))
        if status:
            query = query.filter(Customer.status == status)
        return query
