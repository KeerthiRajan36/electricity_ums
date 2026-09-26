from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.exceptions import UnauthorizedException, ForbiddenException
from app.utils.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedException("Missing bearer token.")

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired access token.")

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None:
        raise UnauthorizedException("User no longer exists.")
    if not user.is_active:
        raise ForbiddenException("This account has been deactivated.")

    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising when no/invalid
    token is supplied. Used by endpoints (e.g. registration) that behave
    differently for anonymous vs. authenticated callers."""
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        return None
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None or not user.is_active:
        return None
    return user


def require_roles(*allowed_roles: UserRole):
    """Dependency factory implementing role-based authorization."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Role '{current_user.role.value}' is not permitted to perform this action."
            )
        return current_user

    return _checker


# Convenience role-group dependencies used across routers
require_super_admin = require_roles(UserRole.SUPER_ADMIN)
require_admin_or_billing = require_roles(UserRole.SUPER_ADMIN, UserRole.BILLING_OFFICER)
require_staff = require_roles(
    UserRole.SUPER_ADMIN,
    UserRole.BILLING_OFFICER,
    UserRole.FIELD_TECHNICIAN,
    UserRole.CUSTOMER_SERVICE_AGENT,
)
require_any_authenticated = get_current_user
