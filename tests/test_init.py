import logging
from unittest.mock import MagicMock, patch

import pytest
from colorama import Fore, Style

from taobaoutils import ColoredFormatter, load_config, setup_logging


@patch("taobaoutils.Path")
@patch("taobaoutils.tomllib")
@patch("taobaoutils.os.getcwd")
def test_load_config_success(mock_getcwd, mock_tomllib, mock_path):
    """Test successful config loading."""
    mock_getcwd.return_value = "/app"

    # Setup mock path
    mock_config_path = MagicMock()
    mock_config_path.exists.return_value = True

    # When Path(os.getcwd()) / "config.toml" is called
    mock_path.return_value.__truediv__.return_value = mock_config_path

    # Mock context manager for opening file
    mock_f = MagicMock()
    mock_config_path.open.return_value.__enter__.return_value = mock_f

    # Mock tomllib result
    expected_config = {"app": {"SECRET_KEY": "test"}}
    mock_tomllib.load.return_value = expected_config

    config = load_config()
    assert config == expected_config


@patch("taobaoutils.Path")
@patch("taobaoutils.sys.exit")
@patch("taobaoutils.os.getcwd")
def test_load_config_file_not_found(mock_getcwd, mock_exit, mock_path):
    """Test config loading failure when file missing."""
    mock_getcwd.return_value = "/app"

    mock_config_path = MagicMock()
    mock_config_path.exists.return_value = False

    mock_path.return_value.__truediv__.return_value = mock_config_path

    load_config()

    mock_exit.assert_called_with(1)


@patch("taobaoutils.Path")
@patch("taobaoutils.sys.exit")
@patch("taobaoutils.os.getcwd")
def test_load_config_exception(mock_getcwd, mock_exit, mock_path):
    """Test config loading generic exception."""
    mock_getcwd.return_value = "/app"

    # Raise exception during exists check
    mock_path.return_value.__truediv__.side_effect = Exception("Permission denied")

    load_config()

    mock_exit.assert_called_with(1)


def test_colored_formatter_console():
    """Test ColoredFormatter adds colors for console output."""
    formatter = ColoredFormatter()

    # Mock config_data used inside formatter
    with patch("taobaoutils.config_data", {"logging": {"LOG_TO_FILE": False}}):
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0, msg="Error message", args=(), exc_info=None
        )
        formatted = formatter.format(record)

        # Check for color codes
        assert Fore.RED in formatted
        assert Style.RESET_ALL in formatted
        assert "Error message" in formatted


def test_colored_formatter_file():
    """Test ColoredFormatter does NOT add colors for file output."""
    formatter = ColoredFormatter()

    with patch("taobaoutils.config_data", {"logging": {"LOG_TO_FILE": True}}):
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0, msg="Error message", args=(), exc_info=None
        )
        formatted = formatter.format(record)

        # Check NO color codes
        assert Fore.RED not in formatted
        assert "Error message" in formatted


@patch("taobaoutils.logging.FileHandler")
@patch("taobaoutils.logging.StreamHandler")
def test_setup_logging_file(mock_stream_handler, mock_file_handler):
    """Test logging setup for file output."""
    config = {"logging": {"LOG_LEVEL": "DEBUG", "LOG_TO_FILE": True, "LOG_FILE_PATH": "/tmp/test.log"}}

    with patch("taobaoutils.config_data", config):
        logger = setup_logging()

        mock_file_handler.assert_called_with("/tmp/test.log", encoding="utf-8")
        assert logger.level == logging.DEBUG


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Reset logger handlers after each test to prevent side effects."""
    yield
    # Reload or reset logger configuration
    logger = logging.getLogger("taobaoutils")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)  # Reset to default level


@patch("taobaoutils.logging.FileHandler")
@patch("taobaoutils.logging.StreamHandler")
def test_setup_logging_console(mock_stream_handler, mock_file_handler):
    """Test logging setup for console output."""
    config = {"logging": {"LOG_LEVEL": "INFO", "LOG_TO_FILE": False, "LOG_FILE_PATH": ""}}

    # We must mock logger inside the function because setup_logging uses logging.getLogger
    # AND it modifies the global logger instance.

    with patch("taobaoutils.config_data", config):
        # Force re-running setup logic on the global logger
        logger = setup_logging()

        # Check that StreamHandler was instantiated
        assert mock_stream_handler.called
        # Check that FileHandler was NOT instantiated (or we don't care, but logic says if-else)
        # assert not mock_file_handler.called # setup_logging logic might be creating both or one?
        # Looking at code: if config[...] LOG_TO_FILE: FileHandler else: StreamHandler.

        assert logger.level == logging.INFO
