import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)) + "/core")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# Use SQLite in-memory for tests (no PostgreSQL required for unit/integration tests)
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=False)
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
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Helper fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def registered_student(client):
    resp = client.post("/auth/register", json={
        "full_name": "Ana García",
        "email": "ana@universidad.edu",
        "password": "password123",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def student_token(client, registered_student):
    resp = client.post("/auth/login", json={
        "email": "ana@universidad.edu",
        "password": "password123",
    })
    return resp.json()["access_token"]


@pytest.fixture
def admin_user(client, db_session):
    import models
    from core.security import hash_password
    admin = models.User(
        full_name="Admin Sistema",
        email="admin@universidad.edu",
        hashed_password=hash_password("admin1234"),
        role=models.UserRole.SPACE_ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_token(client, admin_user):
    resp = client.post("/auth/login", json={
        "email": "admin@universidad.edu",
        "password": "admin1234",
    })
    return resp.json()["access_token"]


@pytest.fixture
def sample_space(client, admin_token):
    resp = client.post("/spaces", json={
        "name": "Laboratorio A-101",
        "type": "LABORATORY",
        "capacity": 30,
        "location": "Edificio A, Piso 1",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    return resp.json()
