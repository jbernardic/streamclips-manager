import os
import dotenv
dotenv.load_dotenv()

from fastapi.testclient import TestClient
from app.main import app
import pytest


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin_token(client):
    response = client.post("/auth/login", json={"username": "admin", "password": os.getenv("ADMIN_PASSWORD")})
    return response.json().get("access_token")