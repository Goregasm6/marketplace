import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from api.main import app
from api.deps import get_db

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_db_override():
        return session

    app.dependency_overrides[get_db] = get_db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to MAIE API", "docs": "/docs"}

def test_list_listings_empty(client: TestClient):
    response = client.get("/listings/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_listing(client: TestClient):
    response = client.post(
        "/listings/",
        json={
            "title": "Test Listing",
            "price": 100.0,
            "source": "test",
            "external_id": "test-1",
            "url": "http://test.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Listing"
    assert data["price"] == 100.0
    assert "id" in data

def test_get_config(client: TestClient):
    response = client.get("/config/")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "ai_api_key" not in data

def test_list_collectors(client: TestClient):
    response = client.get("/collectors/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one collector if they are discovered
    assert len(data) > 0

def test_list_categories(client: TestClient):
    response = client.get("/categories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_scheduler_status(client: TestClient):
    response = client.get("/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
