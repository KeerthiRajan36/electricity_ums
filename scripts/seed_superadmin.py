"""
Bootstraps the very first Super Admin account.

The public /auth/register endpoint deliberately refuses to create staff
accounts (including super_admin) unless the caller is already an
authenticated Super Admin — that's the correct rule once the system is
running, but it means *something* has to create the first one. This script
does that, directly against the database, and is meant to be run exactly
once per fresh install:

    python -m scripts.seed_superadmin

It is idempotent: running it again when a super_admin already exists is a
no-op.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        if existing:
            print(f"A Super Admin already exists: {existing.email}. Nothing to do.")
            return

        email = input("Super Admin email [admin@utility.com]: ").strip() or "admin@utility.com"
        password = input("Super Admin password [Admin@12345]: ").strip() or "Admin@12345"

        user = User(
            full_name="System Administrator",
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Super Admin created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
