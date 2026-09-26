import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
import app.models  # noqa: F401  register all models
from app.main import app
from app.models.user import User, UserRole
from app.utils.security import hash_password

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    import app.services.notification_service as notification_service

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # BackgroundTasks (e.g. notifications) open their own session via
    # notification_service.SessionLocal. Point that at the same in-memory
    # test engine so background work during a test doesn't touch the real
    # on-disk dev database.
    original_session_local = notification_service.SessionLocal
    notification_service.SessionLocal = TestingSessionLocal

    with TestClient(app) as c:
        yield c

    notification_service.SessionLocal = original_session_local
    app.dependency_overrides.clear()


@pytest.fixture()
def super_admin_token(db_session, client):
    user = User(
        full_name="Test Admin",
        email="admin@test.com",
        hashed_password=hash_password("Admin@12345"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    r = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin@12345"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture()
def auth_headers(super_admin_token):
    return {"Authorization": f"Bearer {super_admin_token}"}
