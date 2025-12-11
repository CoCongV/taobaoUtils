import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from taobaoutils.utils import send_request


@pytest.fixture
def mock_config_data():
    with patch("taobaoutils.utils.config_data", {}) as mock_config:
        yield mock_config


def test_send_request_success(mock_config_data):
    """Test successful request with valid JSON response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 800, "msg": "success"}

    with patch("taobaoutils.utils.requests.post", return_value=mock_response) as mock_post:
        success, content = send_request("http://test.com", {"data": 1})

        assert success is True
        assert '"code": 800' in content
        mock_post.assert_called_once()


def test_send_request_http_error(mock_config_data):
    """Test request with HTTP error response."""
    with patch("taobaoutils.utils.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.HTTPError("404 Client Error")

        success, content = send_request("http://test.com", {})

        assert success is False
        assert "404 Client Error" in content


def test_send_request_connection_error(mock_config_data):
    """Test request with connection error."""
    with patch("taobaoutils.utils.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        success, content = send_request("http://test.com", {})

        assert success is False
        assert "Connection refused" in content


def test_send_request_invalid_json(mock_config_data):
    """Test response with invalid JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
    mock_response.text = "Invalid JSON"

    with patch("taobaoutils.utils.requests.post", return_value=mock_response):
        success, content = send_request("http://test.com", {})

        assert success is True  # Function still returns True for success status code, just logs warning
        assert content == "Invalid JSON"


def test_send_request_with_cookies_arg(mock_config_data):
    """Test sending request with explicit cookies argument."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch("taobaoutils.utils.requests.post", return_value=mock_response) as mock_post:
        send_request("http://test.com", {}, cookies="a=1; b=2")

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Cookie"] == "a=1; b=2"


def test_send_request_with_config_cookies(mock_config_data):
    """Test sending request with cookies from config."""
    mock_config_data.update({"Appname": "myapp", "Token": "123456"})

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch("taobaoutils.utils.requests.post", return_value=mock_response) as mock_post:
        send_request("http://test.com", {})

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Cookie"] == "appname=myapp; token=123456"


def test_send_request_partial_config_cookies(mock_config_data):
    """Test warning when only partial cookies config exists."""
    mock_config_data.update({"Appname": "myapp"})  # Missing Token

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch("taobaoutils.utils.requests.post", return_value=mock_response) as mock_post:
        send_request("http://test.com", {})

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert "Cookie" not in headers


def test_send_request_custom_headers(mock_config_data):
    """Test sending request with custom headers from config."""
    mock_config_data.update({"custom_headers": {"User-Agent": "TestAgent"}})

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch("taobaoutils.utils.requests.post", return_value=mock_response) as mock_post:
        send_request("http://test.com", {})

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["User-Agent"] == "TestAgent"
