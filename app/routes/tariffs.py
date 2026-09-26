from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin_or_billing, get_current_user
from app.models.user import User
from app.repositories.tariff_repo import TariffRepository
from app.schemas.tariff import TariffCreate, TariffUpdate, TariffOut
from app.services.audit_service import log_action
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])


@router.post("", response_model=TariffOut, status_code=201)
def create_tariff(
    payload: TariffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    tariff = TariffRepository(db).create(payload.model_dump())
    log_action(db, current_user.id, "CREATE", "Tariff", tariff.id)
    return tariff


@router.get("", response_model=list[TariffOut])
def list_tariffs(
    connection_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = TariffRepository(db)
    query = repo.base_query()
    if connection_type:
        query = query.filter(repo.model.connection_type == connection_type)
    if status:
        query = query.filter(repo.model.status == status)
    return query.order_by(repo.model.connection_type, repo.model.minimum_units).all()


@router.put("/{tariff_id}", response_model=TariffOut)
def update_tariff(
    tariff_id: int,
    payload: TariffUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    repo = TariffRepository(db)
    tariff = repo.get(tariff_id)
    if tariff is None:
        raise NotFoundException("Tariff not found.")
    tariff = repo.update(tariff, payload.model_dump(exclude_unset=True))
    log_action(db, current_user.id, "UPDATE", "Tariff", tariff.id)
    return tariff


@router.delete("/{tariff_id}", status_code=204)
def delete_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_billing),
):
    repo = TariffRepository(db)
    tariff = repo.get(tariff_id)
    if tariff is None:
        raise NotFoundException("Tariff not found.")
    repo.delete(tariff, soft=False)
    log_action(db, current_user.id, "DELETE", "Tariff", tariff_id)
    return None
