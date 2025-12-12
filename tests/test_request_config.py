import pytest

from taobaoutils.app import db, guard
from taobaoutils.models import RequestConfig, User


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        user = User(username="testuser", email="test@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        token = guard.encode_jwt_token(user)
        return {"Authorization": f"Bearer {token}"}


def test_get_request_configs_empty(client, auth_headers):
    response = client.get("/api/request-configs", headers=auth_headers)
    assert response.status_code == 200
    assert response.json == []


def test_create_request_config(client, auth_headers):
    data = {
        "name": "Test Config",
        "request_url": "http://example.com/api",
        "taobao_token": "token123",
        "body": {"a": 1},
        "header": {"x": 1},
        "request_interval_minutes": 10,
        "random_min": 5,
        "random_max": 20,
    }
    response = client.post("/api/request-configs", json=data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json["name"] == "Test Config"
    assert response.json["request_url"] == "http://example.com/api"
    assert response.json["request_interval_minutes"] == 10
    assert response.json["random_min"] == 5
    assert response.json["random_max"] == 20


def test_get_request_config_detail(client, auth_headers, app):
    with app.app_context():
        # User created in auth_headers fixture has ID 1 (first user)
        rc = RequestConfig(
            user_id=1, name="Config 1", request_url="http://old.com", request_interval_minutes=8, body={}, header={}
        )
        db.session.add(rc)
        db.session.commit()
        rc_id = rc.id

    response = client.get(f"/api/request-configs/{rc_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["name"] == "Config 1"
    assert response.json["request_url"] == "http://old.com"
    assert response.json["request_interval_minutes"] == 8


def test_update_request_config(client, auth_headers, app):
    with app.app_context():
        rc = RequestConfig(user_id=1, name="Config 1", body={}, header={})
        db.session.add(rc)
        db.session.commit()
        rc_id = rc.id

    data = {
        "name": "Updated Config",
        "request_url": "http://new.com",
        "body": {"b": 2},
        "request_interval_minutes": 5,
    }
    response = client.put(f"/api/request-configs/{rc_id}", json=data, headers=auth_headers)

    assert response.status_code == 200
    assert response.json["name"] == "Updated Config"
    assert response.json["request_url"] == "http://new.com"
    assert response.json["body"] == {"b": 2}
    assert response.json["request_interval_minutes"] == 5


def test_delete_request_config(client, auth_headers, app):
    with app.app_context():
        rc = RequestConfig(user_id=1, name="To Delete", body={}, header={})
        db.session.add(rc)
        db.session.commit()
        rc_id = rc.id

    response = client.delete(f"/api/request-configs/{rc_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deletion
    with app.app_context():
        assert db.session.get(RequestConfig, rc_id) is None
