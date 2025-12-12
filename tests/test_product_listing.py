from unittest.mock import patch

import pytest

from taobaoutils.app import db, guard
from taobaoutils.models import APIToken, ProductListing, RequestConfig, User


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        # Clean up users to allow ensuring known user ID 1
        db.session.query(User).delete()
        user = User(username="testuser", email="test@example.com", password="password")
        db.session.add(user)
        db.session.commit()

        # Create a default request config for testing
        rc = RequestConfig(user_id=user.id, name="Default Config", body={}, header={})
        db.session.add(rc)
        db.session.commit()

        # Create an API Token
        _, token_obj = APIToken.create_token(user_id=user.id, name="TestToken", scopes=["read"])
        db.session.add(token_obj)
        db.session.commit()

        token = guard.encode_jwt_token(user)
        return {
            "Authorization": f"Bearer {token}",
            "X-Request-Config-ID": str(rc.id),
            "X-API-Token-ID": str(token_obj.id),
        }


@patch("taobaoutils.api.resources._send_single_task_to_scheduler")
def test_create_listing_success(mock_send, client, auth_headers, app):
    mock_send.return_value = True
    rc_id = int(auth_headers["X-Request-Config-ID"])

    data = {
        "status": "requested",
        "product_link": "http://example.com/item",
        "listing_code": "CODE123",
        "request_config_id": rc_id,
        "api_token_id": int(auth_headers["X-API-Token-ID"]),
    }

    response = client.post("/api/product-listings", json=data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json["listing_code"] == "CODE123"

    with app.app_context():
        pl = ProductListing.query.filter_by(listing_code="CODE123").first()
        assert pl is not None
        assert pl.request_config_id == rc_id
        # Should be updated to "是否完成" if scheduler send success
        assert pl.status == "是否完成"


@patch("taobaoutils.api.resources._send_single_task_to_scheduler")
def test_create_listing_scheduler_fail(mock_send, client, auth_headers, app):
    mock_send.return_value = False
    rc_id = int(auth_headers["X-Request-Config-ID"])

    data = {
        "status": "requested",
        "product_link": "http://example.com/fail",
        "request_config_id": rc_id,
        "api_token_id": int(auth_headers["X-API-Token-ID"]),
    }

    response = client.post("/api/product-listings", json=data, headers=auth_headers)
    assert response.status_code == 201

    with app.app_context():
        pl = ProductListing.query.filter_by(product_link="http://example.com/fail").first()
        # Status should remain as initially requested (or default pending)
        assert pl.status == "pending"


def test_get_listings(client, auth_headers, app):
    rc_id = int(auth_headers["X-Request-Config-ID"])
    with app.app_context():
        # User 1 created in auth_headers
        pl1 = ProductListing(user_id=1, request_config_id=rc_id, product_link="l1", status="s1")
        pl2 = ProductListing(user_id=1, request_config_id=rc_id, product_link="l2", status="s2")
        db.session.add_all([pl1, pl2])
        db.session.commit()
        pl1_id = pl1.id

    # Get all
    response = client.get("/api/product-listings", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) == 2

    # Get single
    response = client.get(f"/api/product-listings/{pl1_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["product_link"] == "l1"
