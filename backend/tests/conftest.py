"""
Configuración global de pytest.
Crea una BD SQLite en memoria para los tests y expone el client HTTP.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.core.security import get_password_hash
from app.models.usuario import Usuario
from main import app

# ---------------------------------------------------------------------------
# BD SQLite en memoria (aislada por sesión de tests)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Sobrescribir la dependency de BD con la de tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crear todas las tablas antes de los tests y limpiar al final."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="session")
def db_session():
    """Sesión de BD para setup de datos de prueba."""
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="session")
def admin_user(db_session):
    """Crea y retorna el usuario admin de prueba."""
    admin = Usuario(
        username="test_admin",
        email="admin@test.local",
        nombre_completo="Admin Tests",
        rol="admin",
        hashed_password=get_password_hash("testpass123"),
        activo=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="session")
def client(admin_user):
    """TestClient de FastAPI para tests de integración."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    """Retorna los headers de autorización con token JWT del admin."""
    response = client.post(
        "/auth/login",
        data={"username": "test_admin", "password": "testpass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
