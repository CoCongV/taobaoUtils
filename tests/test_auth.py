import pytest

from taobaoutils.app import db, guard
from taobaoutils.models import APIToken, User


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        db.session.query(User).delete()
        user = User(username="auth_user", email="auth@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        token = guard.encode_jwt_token(user)
        return {"Authorization": f"Bearer {token}"}


def test_register(client):
    data = {"username": "newuser", "email": "new@ex.com", "password": "pwd"}
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 201
    assert response.json["user"]["username"] == "newuser"

    # Test duplicate
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 400


def test_login(client, app):
    with app.app_context():
        user = User(username="login_user", email="l@e.com", password="pwd")
        user.set_password("pwd")
        db.session.add(user)
        db.session.commit()

    data = {"username": "login_user", "password": "pwd"}
    response = client.post("/api/auth/login", json=data)
    assert response.status_code == 200
    assert "access_token" in response.json


def test_user_resource_get(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["user"]["username"] == "auth_user"


def test_user_resource_update(client, auth_headers, app):
    data = {"username": "updated_user", "taobao_token": "tb_token"}
    response = client.put("/api/auth/me", json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json["user"]["username"] == "updated_user"

    with app.app_context():
        u = User.query.filter_by(username="updated_user").first()
        assert u.taobao_token == "tb_token"


def test_api_token_crud(client, auth_headers, app):
    # Create
    data = {"name": "Token1", "scopes": ["read"], "expires_days": 30}
    response = client.post("/api/tokens", json=data, headers=auth_headers)
    assert response.status_code == 201
    _token_val = response.json["token"]["token"]
    token_id = response.json["token"]["id"]

    # Get List
    response = client.get("/api/tokens", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json["tokens"]) == 1

    # Get Single
    response = client.get(f"/api/tokens/{token_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["token"]["name"] == "Token1"

    # Update
    data = {"name": "Renamed", "is_active": False}
    response = client.put(f"/api/tokens/{token_id}", json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json["token"]["name"] == "Renamed"
    assert response.json["token"]["is_active"] is False

    # Delete
    response = client.delete(f"/api/tokens/{token_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify Deletion
    with app.app_context():
        assert db.session.get(APIToken, token_id) is None


# Test api_token_required decorator logic using the decorator directly via a route
# Usually we need to integraton test it.
# Or we can create a dummy protected route in the test app.
