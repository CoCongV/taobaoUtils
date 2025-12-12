import os

from flask import Flask
from flask_praetorian import Praetorian
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

from taobaoutils import config_data, logger

db = SQLAlchemy()
api = Api()
guard = Praetorian()  # Praetorian guard 实例


def create_app():
    app = Flask(__name__)

    # Load Flask configuration from config.toml
    app.config["SECRET_KEY"] = config_data["app"].get("SECRET_KEY", "a_very_secret_key_that_should_be_in_conf")
    app.config["SQLALCHEMY_DATABASE_URI"] = config_data["app"].get(
        "DATABASE_URI", f"sqlite:///{os.path.abspath(os.path.join(os.getcwd(), 'taobaoutils.db'))}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Validate essential configuration
    if not config_data.get("scheduler", {}).get("SCHEDULER_SERVICE_URL"):
        logger.warning("SCHEDULER_SERVICE_URL is not configured in config.toml")
        # You might want to raise an error here if it's critical:
        # raise ValueError("SCHEDULER_SERVICE_URL is required")

    # Praetorian 配置
    app.config["JWT_ACCESS_LIFESPAN"] = {"hours": 24}
    app.config["JWT_REFRESH_LIFESPAN"] = {"days": 30}

    db.init_app(app)

    # Import and register blueprints/resources
    from taobaoutils.api.routes import initialize_routes

    # Check if routes are already registered to avoid re-registration in tests
    if not api.resources:
        initialize_routes(api)

    api.init_app(app)

    # 初始化 Praetorian
    from taobaoutils.models import User

    guard.init_app(app, User)

    with app.app_context():
        db.create_all()  # Create database tables for our models

    logger.info("Flask application created and configured.")
    return app
