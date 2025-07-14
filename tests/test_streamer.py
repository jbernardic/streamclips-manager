import uuid
from fastapi.testclient import TestClient


def test_create_streamer_success(created_streamer):
    assert created_streamer["url"] == "https://kick.com/xqc"
    assert created_streamer["name"] == "xqc"
    assert created_streamer["is_active"] == True
    assert "id" in created_streamer

def test_create_streamer_unauthorized(client: TestClient):
    url = "https://kick.com/xqc"
    name = "xqc"
    response = client.post("/streamers", json={"url": url, "name": name})
    assert response.status_code == 401

def test_update_streamer_success(client: TestClient, admin_token: str, created_streamer):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    id = created_streamer["id"]
    name = "test" #updated
    url = created_streamer["url"]
    is_active = False  #updated

    response = client.put("/streamers", json={"id": id, "name": name, "url": url, "is_active": is_active }, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == id
    assert data["name"] == name
    assert data["url"] == url
    assert data["is_active"] == is_active

def test_update_streamer_unauthorized(client: TestClient, created_streamer):
    id = created_streamer["id"]
    name = "test" #updated
    url = created_streamer["url"]
    is_active = False  #updated

    response = client.put("/streamers", json={"id": id, "name": name, "url": url, "is_active": is_active })
    assert response.status_code == 401

def test_delete_streamer_success(client: TestClient, admin_token: str, created_streamer):
    headers = {"Authorization": f"Bearer {admin_token}"}
    id = created_streamer["id"]

    response = client.delete(f"/streamers/{id}", headers=headers)
    assert response.status_code == 200


def test_delete_streamer_unauthorized(client: TestClient, created_streamer):
    id = created_streamer["id"]

    response = client.delete(f"/streamers/{id}")
    assert response.status_code == 401

def test_get_streamer_success(client: TestClient, created_streamer, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    id = created_streamer["id"]
    name = created_streamer["name"]
    url = created_streamer["url"]
    is_active = created_streamer["is_active"]

    response = client.get(f"/streamers/{id}", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["name"] == name
    assert response.json()["url"] == url
    assert response.json()["is_active"] == is_active


def test_get_streamer_unauthorized(client: TestClient):
    response = client.get(f"/streamers/{id}")
    assert response.status_code == 401

def test_list_streamers_success(client: TestClient, admin_token, created_streamer):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(f"/streamers", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data.count(created_streamer) == 1


def test_list_streamers_unauthorized(client: TestClient):
    response = client.get(f"/streamers")
    assert response.status_code == 401