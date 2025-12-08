import json

import pytest

from taobaoutils.app import create_app, db


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use in-memory SQLite for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_get_logs(client):
    """Test fetching all request logs."""
    response = client.get("/logs")
    assert response.status_code == 200
    assert json.loads(response.data) == []


def test_post_log(client):
    """Test adding a new request log."""
    data = {"url": "http://example.com", "status": "success", "response_content": "{}", "response_code": 200}
    response = client.post("/logs", json=data)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert response_data["url"] == "http://example.com"
    assert response_data["status"] == "success"


def test_registration_disabled(client):
    """Test registration when it's disabled."""
    # Assuming config_data['app']['ALLOW_REGISTRATION'] is false by default
    data = {"username": "testuser", "password": "password"}
    response = client.post("/register", json=data)
    assert response.status_code == 403
    assert json.loads(response.data)["message"] == "User registration is currently disabled."
