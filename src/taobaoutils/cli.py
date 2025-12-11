import sys
from pathlib import Path

import click
import pytest

from taobaoutils import logger
from taobaoutils.app import create_app

# Ensure the project root is in sys.path for module imports
# Assuming cli.py is in src/taobaoutils/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


@click.group()
def main():
    """Taobao Utils CLI"""
    pass


@main.command()
@click.option("--host", default="127.0.0.1", help="Host address for the Flask server.")
@click.option("--port", default=5000, type=int, help="Port for the Flask server.")
def serve(host, port):
    """Run the Flask API development server for testing."""
    logger.info("Starting Flask API development server on %s:%s...", host, port)
    try:
        app = create_app()
        app.run(host=host, port=port, debug=True)
    except Exception as e:
        logger.error("Failed to start Flask API development server: %s", e)
        sys.exit(1)


@main.command()
@click.option("--coverage", is_flag=True, default=False, help="Run tests with coverage report.")
def test(coverage):
    """Run tests using pytest."""

    args = []
    if coverage:
        args.extend(["--cov=src/taobaoutils", "--cov-report=term-missing", "--cov-report=html"])

    # Run pytest and exit with its return code
    sys.exit(pytest.main(args))


if __name__ == "__main__":
    main()
