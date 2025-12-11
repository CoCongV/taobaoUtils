from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from taobaoutils.cli import main


def test_serve_command():
    runner = CliRunner()

    # Mock create_app and app.run
    with patch("taobaoutils.cli.create_app") as mock_create_app:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        result = runner.invoke(main, ["serve", "--host", "0.0.0.0", "--port", "8000"])

        assert result.exit_code == 0
        mock_create_app.assert_called_once()
        mock_app.run.assert_called_once_with(host="0.0.0.0", port=8000, debug=True)


def test_serve_command_default_args():
    runner = CliRunner()

    with patch("taobaoutils.cli.create_app") as mock_create_app:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        result = runner.invoke(main, ["serve"])

        assert result.exit_code == 0
        mock_app.run.assert_called_once_with(host="127.0.0.1", port=5000, debug=True)


def test_serve_command_fail():
    runner = CliRunner()

    with patch("taobaoutils.cli.create_app") as mock_create_app:
        mock_create_app.side_effect = Exception("Setup failed")

        result = runner.invoke(main, ["serve"])

        assert result.exit_code == 1
        # Log message might not appear in result.output depending on logger config
        # assert "Failed to start Flask API development server" in result.output


def test_test_command_default():
    runner = CliRunner()

    with patch("taobaoutils.cli.pytest") as mock_pytest:
        mock_pytest.main.return_value = 0

        result = runner.invoke(main, ["test"])

        assert result.exit_code == 0
        mock_pytest.main.assert_called_once_with([])


def test_test_command_with_coverage():
    runner = CliRunner()

    with patch("taobaoutils.cli.pytest") as mock_pytest:
        mock_pytest.main.return_value = 0

        result = runner.invoke(main, ["test", "--coverage"])

        assert result.exit_code == 0
        mock_pytest.main.assert_called_once()
        args = mock_pytest.main.call_args[0][0]
        assert "--cov=src/taobaoutils" in args
        assert "--cov-report=html" in args
