from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SELF_REGISTERABLE_ROLES
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest
from app.utils.exceptions import ConflictException, UnauthorizedException, ForbiddenException, BadRequestException
from app.utils.security import hash_password, verify_password, decode_token


def register_user(db: Session, data: RegisterRequest, actor: User | None) -> User:
    repo = UserRepository(db)

    if data.role not in SELF_REGISTERABLE_ROLES:
        # Creating a staff account requires an authenticated Super Admin.
        if actor is None or actor.role != UserRole.SUPER_ADMIN:
            raise ForbiddenException(
                "Only a Super Admin can create staff accounts. Register as a customer instead."
            )

    if repo.get_by_email(data.email):
        raise ConflictException(f"Email '{data.email}' is already registered.")

    user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        customer_id=data.customer_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password.")
    if not user.is_active:
        raise ForbiddenException("This account has been deactivated.")
    return user


def rotate_refresh_token(db: Session, refresh_token: str) -> User:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid or expired refresh token.")

    repo = UserRepository(db)
    user = repo.get_by_email(payload.get("sub"))
    if user is None or not user.is_active:
        raise UnauthorizedException("User no longer exists or is inactive.")
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.hashed_password):
        raise BadRequestException("Old password is incorrect.")
    user.hashed_password = hash_password(new_password)
    db.commit()


def set_active_status(db: Session, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
