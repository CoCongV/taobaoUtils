import sys
from pathlib import Path

import click

from taobaoutils import logger

# Ensure the project root is in sys.path for module imports
# Assuming cli.py is in src/taobaoutils/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


@click.group()
def main():
    """Taobao Utils CLI"""
    pass


@main.command()
@click.option('--host', default='127.0.0.1', help='Host address for the Flask server.')
@click.option('--port', default=5000, type=int, help='Port for the Flask server.')
def serve(host, port):
    """Run the Flask API development server for testing."""
    logger.info("Starting Flask API development server on %s:%s...", host, port)
    try:
        from taobaoutils.app import create_app
        app = create_app()
        app.run(host=host, port=port, debug=True)
    except Exception as e:
        logger.error("Failed to start Flask API development server: %s", e)
        sys.exit(1)

@main.command(name="process")
@click.argument('excel_path', type=click.Path(exists=True, dir_okay=False, readable=True))
def process_excel_command(excel_path):
    """Process the Excel file specified by path."""
    logger.info("Processing Excel file: %s...", excel_path)
    from taobaoutils.excel_processor import process_excel_main
    process_excel_main(excel_path)


if __name__ == '__main__':
    main()
