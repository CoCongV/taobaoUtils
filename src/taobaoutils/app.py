import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from taobaoutils import config_data, logger


db = SQLAlchemy()
api = Api()

def create_app():
    app = Flask(__name__)

    # Load Flask configuration from config.toml
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_in_env') # Fallback for development
    app.config['SQLALCHEMY_DATABASE_URI'] = config_data['app'].get('DATABASE_URI', 'sqlite:///taobaoutils.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    api.init_app(app)

    # Import and register blueprints/resources
    from taobaoutils.routes import initialize_routes
    initialize_routes(api)

    with app.app_context():
        db.create_all() # Create database tables for our models

    logger.info("Flask application created and configured.")
    return app