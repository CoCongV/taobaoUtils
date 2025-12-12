import pytest

from taobaoutils.app import db
from taobaoutils.models import APIToken, ProductListing, RequestConfig, User


@pytest.fixture
def api_auth_headers(app):
    with app.app_context():
        # Clean users to ensure unique username
        db.session.query(User).delete()
        user = User(username="cb_user", email="cb@ex.com", password="pwd")
        db.session.add(user)
        db.session.commit()

        token_str, token = APIToken.create_token(user.id, "TestToken", scopes=["read"], expires_days=30)
        db.session.add(token)
        db.session.commit()
        return {"Authorization": f"Bearer {token_str}", "X-API-Token-ID": str(token.id)}


def test_callback_success(client, api_auth_headers, app):
    with app.app_context():
        user = User.query.filter_by(username="cb_user").first()
        # Create RequestConfig
        rc = RequestConfig(user_id=user.id, name="Callback Config", body={}, header={})
        db.session.add(rc)
        db.session.commit()

        pl = ProductListing(
            user_id=user.id,
            request_config_id=rc.id,
            product_id="123",
            api_token_id=int(api_auth_headers["X-API-Token-ID"]),
        )
        db.session.add(pl)
        db.session.commit()
        pl_id = pl.id

    data = {"id": pl_id, "status": "completed", "response_code": 200, "response_content": "ok"}

    # Use real headers
    response = client.post("/api/scheduler/callback", json=data, headers=api_auth_headers)

    assert response.status_code == 200

    with app.app_context():
        pl = db.session.get(ProductListing, pl_id)
        assert pl.status == "completed"
        assert pl.response_code == 200
        assert pl.response_content == "ok"


def test_callback_not_found(client, api_auth_headers):
    data = {"id": 99999, "status": "completed"}
    response = client.post("/api/scheduler/callback", json=data, headers=api_auth_headers)
    assert response.status_code == 404


def test_callback_missing_args(client, api_auth_headers):
    data = {"status": "completed"}
    response = client.post("/api/scheduler/callback", json=data, headers=api_auth_headers)
    assert response.status_code == 400


def test_callback_partial_update(client, api_auth_headers, app):
    with app.app_context():
        user = User.query.filter_by(username="cb_user").first()
        rc = RequestConfig(user_id=user.id, name="Callback Config 2", body={}, header={})
        db.session.add(rc)
        db.session.commit()

        pl = ProductListing(user_id=user.id, request_config_id=rc.id, status="pending", product_id="456")
        db.session.add(pl)
        db.session.commit()
        pl_id = pl.id

    data = {"id": pl_id, "status": "failed"}
    response = client.post("/api/scheduler/callback", json=data, headers=api_auth_headers)
    assert response.status_code == 200

    with app.app_context():
        pl = db.session.get(ProductListing, pl_id)
        assert pl.status == "failed"
        assert pl.response_code is None
