from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_optional_current_user, require_super_admin
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.utils.exceptions import NotFoundException
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshRequest, ChangePasswordRequest, TokenResponse, UserOut
)
from app.services import auth_service
from app.services.audit_service import log_action
from app.utils.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    actor: User | None = Depends(get_optional_current_user),
):
    user = auth_service.register_user(db, payload, actor)
    log_action(db, actor.id if actor else None, "CREATE", "User", user.id, f"Registered role={user.role.value}")
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    log_action(db, user.id, "LOGIN", "User", user.id)
    return TokenResponse(
        access_token=create_access_token(user.email, user.role.value),
        refresh_token=create_refresh_token(user.email, user.role.value),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    user = auth_service.rotate_refresh_token(db, payload.refresh_token)
    return TokenResponse(
        access_token=create_access_token(user.email, user.role.value),
        refresh_token=create_refresh_token(user.email, user.role.value),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.change_password(db, current_user, payload.old_password, payload.new_password)
    log_action(db, current_user.id, "UPDATE", "User", current_user.id, "Password changed")
    return None


@router.put("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_super_admin)):
    user = UserRepository(db).get(user_id)
    if user is None:
        raise NotFoundException("User not found.")
    user = auth_service.set_active_status(db, user, True)
    log_action(db, admin.id, "UPDATE", "User", user.id, "Activated account")
    return user


@router.put("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_super_admin)):
    user = UserRepository(db).get(user_id)
    if user is None:
        raise NotFoundException("User not found.")
    user = auth_service.set_active_status(db, user, False)
    log_action(db, admin.id, "UPDATE", "User", user.id, "Deactivated account")
    return user
