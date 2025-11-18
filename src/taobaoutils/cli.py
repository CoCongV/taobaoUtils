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
@click.option('--workers', default=1, type=int, help='Number of Gunicorn worker processes.')
def serve(host, port, workers):
    """Run the Flask API server."""
    logger.info("Starting Flask API server on %s:%s with %s workers...", host, port, workers)
    try:
        from taobaoutils.app import create_app
        app = create_app()
        
        # Use Gunicorn to serve the Flask app
        # This requires gunicorn to be installed
        from gunicorn.app.base import BaseApplication

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            'bind': f'{host}:{port}',
            'workers': workers,
            # Use the configured log level
            'loglevel': logger.level,
            # Log to stdout
            'accesslog': '-',
            # Log to stderr
            'errorlog': '-',
        }
        StandaloneApplication(app, options).run()

    except ImportError:
        logger.error("Gunicorn is not installed. Please install it with 'poetry add gunicorn'.")
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to start Flask API server: %s", e)
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
