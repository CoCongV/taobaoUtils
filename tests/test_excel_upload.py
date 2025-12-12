from io import BytesIO
from unittest.mock import patch

import pandas as pd
import pytest

from taobaoutils.app import db, guard
from taobaoutils.models import APIToken, ProductListing, RequestConfig, User


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        # Ensure user exists
        user = User(username="excel_user", email="excel@example.com", password="password")
        db.session.add(user)
        db.session.commit()

        # Create RequestConfig
        rc = RequestConfig(user_id=user.id, name="Excel Config", body={}, header={})
        db.session.add(rc)
        db.session.commit()

        # Create Test Token
        _, token_obj = APIToken.create_token(user_id=user.id, name="TestToken", scopes=["read"])
        db.session.add(token_obj)
        db.session.commit()

        token = guard.encode_jwt_token(user)
        return {
            "Authorization": f"Bearer {token}",
            "X-Request-Config-ID": str(rc.id),
            "X-API-Token-ID": str(token_obj.id),
        }


@patch("taobaoutils.api.resources._send_batch_tasks_to_scheduler")
def test_upload_excel_success(mock_send_batch, client, auth_headers, app):
    mock_send_batch.return_value = True
    rc_id = auth_headers["X-Request-Config-ID"]

    # Create valid excel file in memory
    df = pd.DataFrame(
        {
            "商品ID": ["111", "222"],
            "商品链接": ["http://l1", "http://l2"],
            "标题": ["T1", "T2"],
            "库存": [10, 20],
            "上架编码": ["C1", "C2"],
        }
    )

    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    data = {
        "file": (excel_file, "test.xlsx"),
        "request_config_id": rc_id,
        "api_token_id": auth_headers.get("X-API-Token-ID", "1"),
    }

    response = client.post(
        "/api/product-listings/upload", data=data, content_type="multipart/form-data", headers=auth_headers
    )
    assert response.status_code == 201
    assert "processed 2 product listings" in response.json["message"]

    with app.app_context():
        assert ProductListing.query.count() == 2
        pl = ProductListing.query.filter_by(product_id="111").first()
        assert pl.status == "是否完成"  # Should be updated after callback


@patch("taobaoutils.api.resources._send_batch_tasks_to_scheduler")
def test_upload_excel_scheduler_fail(mock_send_batch, client, auth_headers, app):
    mock_send_batch.return_value = False
    rc_id = auth_headers["X-Request-Config-ID"]

    df = pd.DataFrame({"商品ID": ["333"], "商品链接": ["http://l3"], "标题": ["T3"], "库存": [30], "上架编码": ["C3"]})

    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    data = {
        "file": (excel_file, "fails.xlsx"),
        "request_config_id": rc_id,
        "api_token_id": auth_headers.get("X-API-Token-ID", "1"),
    }

    response = client.post(
        "/api/product-listings/upload", data=data, content_type="multipart/form-data", headers=auth_headers
    )
    assert response.status_code == 201

    with app.app_context():
        pl = ProductListing.query.filter_by(product_id="333").first()
        # Status remains "Uploaded" if scheduler send fails
        assert pl.status == "Uploaded"


def test_upload_invalid_file_type(client, auth_headers):
    data = {
        "file": (BytesIO(b"dummy"), "test.txt"),
        "request_config_id": auth_headers.get("X-Request-Config-ID", "1"),
        "api_token_id": auth_headers.get("X-API-Token-ID", "1"),
    }
    response = client.post(
        "/api/product-listings/upload", data=data, content_type="multipart/form-data", headers=auth_headers
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json["message"]


def test_upload_missing_headers(client, auth_headers):
    df = pd.DataFrame({"WrongHeader": [1]})
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    data = {
        "file": (excel_file, "bad.xlsx"),
        "request_config_id": auth_headers.get("X-Request-Config-ID", "1"),
        "api_token_id": auth_headers.get("X-API-Token-ID", "1"),
    }
    response = client.post(
        "/api/product-listings/upload", data=data, content_type="multipart/form-data", headers=auth_headers
    )
    assert response.status_code == 400
    assert "Missing required headers" in response.json["message"]
