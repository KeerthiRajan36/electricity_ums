from typing import Generic, List, TypeVar, Sequence

from pydantic import BaseModel
from sqlalchemy import asc, desc
from sqlalchemy.orm import Query

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20
    sort_by: str | None = None
    sort_order: str = "asc"  # "asc" | "desc"


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    limit: int
    pages: int
    items: List[T]


def apply_sorting(query: Query, model, sort_by: str | None, sort_order: str = "asc") -> Query:
    if sort_by and hasattr(model, sort_by):
        column = getattr(model, sort_by)
        query = query.order_by(desc(column) if sort_order == "desc" else asc(column))
    return query


def paginate(query: Query, page: int, limit: int) -> tuple[Sequence, int]:
    page = max(page, 1)
    limit = max(min(limit, 200), 1)
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total


def build_paginated_response(items, total: int, page: int, limit: int) -> dict:
    pages = (total + limit - 1) // limit if limit else 0
    return {"total": total, "page": page, "limit": limit, "pages": pages, "items": items}
