from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import RequestException

from taobaoutils.api.resources import (
    _get_payload_from_listing,
    _send_batch_tasks_to_scheduler,
    _send_single_task_to_scheduler,
)
from taobaoutils.models import ProductListing


@pytest.fixture
def mock_listing():
    listing = MagicMock(spec=ProductListing)
    listing.id = 1
    listing.product_link = "http://test.com/?id=123"
    listing.listing_code = "CODE1"
    listing.request_config = MagicMock()
    listing.request_config.request_url = "http://target"
    listing.request_config.request_interval_minutes = 1
    listing.request_config.random_min = 2
    listing.request_config.random_max = 3
    return listing


@pytest.fixture
def mock_config():
    return {
        "request_payload_template": {"some_field": "val", "linkData": [{"url": "{url}", "num_iid": ""}]},
        "scheduler": {"SCHEDULER_SERVICE_URL": "http://scheduler"},
        "custom_headers": {"Cookie": "abc"},
        "TARGET_URL": "http://target",
        "REQUEST_INTERVAL_MINUTES": 1,
        "RANDOM_INTERVAL_SECONDS_MIN": 0,
        "RANDOM_INTERVAL_SECONDS_MAX": 0,
    }


# --- Test _get_payload_from_listing ---


def test_get_payload_extraction(mock_listing, mock_config):
    with patch("taobaoutils.api.resources.config_data", mock_config):
        payload = _get_payload_from_listing(mock_listing)

        assert payload["linkData"][0]["url"] == "http://test.com/?id=123"
        assert payload["linkData"][0]["num_iid"] == "123"


def test_get_payload_no_id(mock_listing, mock_config):
    mock_listing.product_link = "http://test.com/noid"
    with patch("taobaoutils.api.resources.config_data", mock_config):
        payload = _get_payload_from_listing(mock_listing)
        assert payload["linkData"][0]["num_iid"] == ""


def test_get_payload_malformed_template(mock_listing):
    # Template without linkData
    config = {"request_payload_template": {"foo": "bar"}}
    with patch("taobaoutils.api.resources.config_data", config):
        payload = _get_payload_from_listing(mock_listing)
        assert payload["foo"] == "bar"
        assert "linkData" not in payload


# --- Test _send_single_task_to_scheduler ---


@patch("taobaoutils.api.resources.requests.post")
def test_send_single_task_success(mock_post, mock_listing, mock_config):
    mock_post.return_value.raise_for_status = MagicMock()

    with patch("taobaoutils.api.resources.config_data", mock_config):
        result = _send_single_task_to_scheduler(mock_listing)

        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["target_url"] == "http://target"


@patch("taobaoutils.api.resources.requests.post")
def test_send_single_task_with_request_config(mock_post, mock_listing, mock_config):
    mock_post.return_value.raise_for_status = MagicMock()

    # Mock RequestConfig
    req_config = MagicMock()
    req_config.request_url = "http://custom-target"
    req_config.request_interval_minutes = 10
    req_config.random_min = 5
    req_config.random_max = 20
    mock_listing.request_config = req_config

    with patch("taobaoutils.api.resources.config_data", mock_config):
        result = _send_single_task_to_scheduler(mock_listing)

        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        json_data = kwargs["json"]
        assert json_data["target_url"] == "http://custom-target"
        assert json_data["request_interval_minutes"] == 10
        assert json_data["random_min"] == 5
        assert json_data["random_max"] == 20


@patch("taobaoutils.api.resources.requests.post")
def test_send_single_task_no_config(mock_post, mock_listing, mock_config):
    mock_listing.request_config = None
    with patch("taobaoutils.api.resources.config_data", mock_config):
        result = _send_single_task_to_scheduler(mock_listing)
        assert result is False
        mock_post.assert_not_called()


@patch("taobaoutils.api.resources.requests.post")
def test_send_single_task_failure(mock_post, mock_listing, mock_config):
    mock_post.side_effect = RequestException("Error")

    with patch("taobaoutils.api.resources.config_data", mock_config):
        assert _send_single_task_to_scheduler(mock_listing) is False


# --- Test _send_batch_tasks_to_scheduler ---


@patch("taobaoutils.api.resources.requests.post")
def test_send_batch_tasks_success(mock_post, mock_listing, mock_config):
    mock_post.return_value.raise_for_status = MagicMock()
    listings = [mock_listing, mock_listing]

    with patch("taobaoutils.api.resources.config_data", mock_config):
        result = _send_batch_tasks_to_scheduler(listings)

        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert len(kwargs["json"]["payloads"]) == 2


@patch("taobaoutils.api.resources.requests.post")
def test_send_batch_tasks_failure(mock_post, mock_listing, mock_config):
    mock_post.side_effect = RequestException("Error")

    with patch("taobaoutils.api.resources.config_data", mock_config):
        assert _send_batch_tasks_to_scheduler([mock_listing]) is False
