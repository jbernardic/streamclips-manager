
import dotenv
dotenv.load_dotenv(override=True)

import os
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database import connection

from fastapi.testclient import TestClient
from app.main import app
import pytest

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    connection.SessionLocal = TestingSessionLocal
    yield
    Base.metadata.drop_all(bind=engine)
    connection.SessionLocal = None

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin_token(client: TestClient):
    response = client.post(
        "/auth/login",
        data={  # Note: `data` not `json`
            "username": "admin",
            "password": os.getenv("ADMIN_PASSWORD", "defaultpassword")
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture
def created_streamer(client: TestClient, admin_token: str):
    url = "https://kick.com/xqc"
    name = "xqc"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.post("/streamers", json={"url": url, "name": name}, headers=headers)
    return response.json()