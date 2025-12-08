from click.testing import CliRunner

from taobaoutils.cli import main


def test_main_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output


def test_serve_command_help():
    runner = CliRunner()
    result = runner.invoke(main, ["serve", "--help"])
    assert result.exit_code == 0
    assert "Run the Flask API server." in result.output


def test_process_excel_command_help():
    runner = CliRunner()
    result = runner.invoke(main, ["process-excel", "--help"])
    assert result.exit_code == 0
    assert "Process the Excel file in the current directory." in result.output


# Note: Actual testing of 'serve' and 'process-excel' commands would require
# mocking external dependencies (Flask app, Gunicorn, Excel file operations, requests).
# These are basic tests to ensure the CLI structure is working.
