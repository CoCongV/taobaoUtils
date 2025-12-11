from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from taobaoutils.excel_processor import load_excel_data, process_row_logic, save_dataframe, validate_columns


@pytest.fixture
def mock_config():
    config = {
        "URL_COLUMN": "Link",
        "STATUS_COLUMN": "Status",
        "SEND_TIME_COLUMN": "Last Sent",
        "RESPONSE_COLUMN": "Response",
        "STATUS_SUCCESS_VALUE": "Done",
        "REQUEST_INTERVAL_MINUTES": 1,
        "RANDOM_INTERVAL_SECONDS_MIN": 0,
        "RANDOM_INTERVAL_SECONDS_MAX": 0,
        "TARGET_URL": "http://api.test",
        "request_payload_template": {"some_field": "value", "linkData": [{"url": "{url}", "num_iid": ""}]},
    }
    with patch("taobaoutils.excel_processor.config_data", config) as mock:
        yield mock


@pytest.fixture
def sample_df():
    return pd.DataFrame({"Link": ["http://test.com/id=1"], "Status": [""], "Last Sent": [None], "Response": [""]})


def test_process_row_logic_skip_empty_url(mock_config, sample_df):
    """Test skipping row with empty URL."""
    sample_df.at[0, "Link"] = ""
    last_send_time = None

    new_last_time, processed = process_row_logic(sample_df, 0, sample_df.iloc[0], last_send_time)

    assert processed is False
    assert new_last_time is None


def test_process_row_logic_skip_success_status(mock_config, sample_df):
    """Test skipping row with success status."""
    sample_df.at[0, "Status"] = "Done"
    last_send_time = None

    new_last_time, processed = process_row_logic(sample_df, 0, sample_df.iloc[0], last_send_time)

    assert processed is False
    assert new_last_time is None


@patch("taobaoutils.excel_processor.send_request")
@patch("taobaoutils.excel_processor.time.sleep")
def test_process_row_logic_send_request(mock_sleep, mock_send, mock_config, sample_df):
    """Test processing a row and sending a request."""
    mock_send.return_value = (True, "OK")
    last_send_time = None

    new_last_time, processed = process_row_logic(sample_df, 0, sample_df.iloc[0], last_send_time)

    assert processed is True
    assert isinstance(new_last_time, datetime)
    assert sample_df.at[0, "Status"] == "Done"
    assert sample_df.at[0, "Response"] == "OK"

    # Verify payload construction
    expected_payload = {"some_field": "value", "linkData": [{"url": "http://test.com/id=1", "num_iid": "1"}]}
    mock_send.assert_called_with("http://api.test", expected_payload)


@patch("taobaoutils.excel_processor.send_request")
@patch("taobaoutils.excel_processor.time.sleep")
@patch("taobaoutils.excel_processor.datetime")
def test_process_row_logic_wait_interval(mock_datetime, mock_sleep, mock_send, mock_config, sample_df):
    """Test waiting interval between requests."""
    mock_send.return_value = (True, "OK")

    # Mock current time: 2023-01-01 10:00:30
    now = datetime(2023, 1, 1, 10, 0, 30)
    mock_datetime.now.return_value = now

    # Last sent: 2023-01-01 10:00:00 (30 seconds ago)
    # Interval is 1 min (60s), so should wait ~30s
    last_send_time = datetime(2023, 1, 1, 10, 0, 0)

    new_last_time, processed = process_row_logic(sample_df, 0, sample_df.iloc[0], last_send_time)

    assert processed is True
    assert mock_sleep.called
    # Check that sleep was called with a value close to 30 (ignoring random jitter which is 0 in mock)
    args, _ = mock_sleep.call_args
    assert 29 <= args[0] <= 31


@patch("taobaoutils.excel_processor.pd.read_excel")
def test_load_excel_data_success(mock_read_excel, mock_config):
    """Test loading excel data successfully."""
    # Mock return DataFrame
    df = pd.DataFrame({"Link": ["url1"], "Other": [1]})
    mock_read_excel.return_value = df

    result_df = load_excel_data("dummy.xlsx")

    assert "Status" in result_df.columns
    assert "Last Sent" in result_df.columns
    assert "Response" in result_df.columns
    assert mock_read_excel.called


@patch("taobaoutils.excel_processor.sys.exit")
@patch("taobaoutils.excel_processor.pd.read_excel")
def test_load_excel_data_file_not_found(mock_read_excel, mock_exit, mock_config):
    """Test loading non-existent excel file."""
    mock_read_excel.side_effect = FileNotFoundError

    load_excel_data("missing.xlsx")

    mock_exit.assert_called_with(1)


def test_validate_columns_success(mock_config):
    """Test validating correct columns."""
    df = pd.DataFrame(columns=["Link", "Status", "Last Sent", "Response"])
    # Should not raise exception
    validate_columns(df)


@patch("taobaoutils.excel_processor.sys.exit")
def test_validate_columns_failure(mock_exit, mock_config):
    """Test validating missing columns."""
    df = pd.DataFrame(columns=["Link"])  # Missing others

    validate_columns(df)

    mock_exit.assert_called_with(1)


@patch("taobaoutils.excel_processor.pd.DataFrame.to_excel")
def test_save_dataframe(mock_to_excel, mock_config, sample_df):
    """Test saving dataframe."""
    # Ensure Last Sent is datetime
    sample_df["Last Sent"] = pd.to_datetime(sample_df["Last Sent"])

    save_dataframe(sample_df, 0, "out.xlsx")

    mock_to_excel.assert_called()
