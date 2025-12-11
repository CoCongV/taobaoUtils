from unittest.mock import patch

from taobaoutils.app import create_app


@patch("taobaoutils.app.config_data", {"app": {"SECRET_KEY": "test_sec", "DATABASE_URI": "sqlite:///custom.db"}})
@patch("taobaoutils.app.db.init_app")
@patch("taobaoutils.app.api.init_app")
@patch("taobaoutils.app.guard.init_app")
@patch("taobaoutils.app.db.create_all")
def test_create_app_custom_config(mock_create_all, mock_guard_init, mock_api_init, mock_db_init):
    """Test create_app with custom configuration."""
    app = create_app()

    assert app.config["SECRET_KEY"] == "test_sec"
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///custom.db"

    mock_db_init.assert_called_once()
    mock_api_init.assert_called_once()
    mock_guard_init.assert_called_once()
    mock_create_all.assert_called_once()


@patch("taobaoutils.app.config_data", {"app": {}})  # Missing optional keys
@patch("taobaoutils.app.db.init_app")
@patch("taobaoutils.app.api.init_app")
@patch("taobaoutils.app.guard.init_app")
@patch("taobaoutils.app.db.create_all")
def test_create_app_defaults(mock_create_all, mock_guard_init, mock_api_init, mock_db_init):
    """Test create_app default values."""
    app = create_app()

    assert "SECRET_KEY" in app.config
    assert "taobaoutils.db" in app.config["SQLALCHEMY_DATABASE_URI"]


@patch("taobaoutils.app.config_data", {"app": {}})
@patch("taobaoutils.app.api")
def test_create_app_skip_routes(mock_api):
    """Test that routes are not re-registered if already present."""
    # Simulate routes already existing
    mock_api.resources = ["some_resource"]

    # Needs many mocks to pass through the function
    with (
        patch("taobaoutils.app.db"),
        patch("taobaoutils.app.guard"),
        patch("taobaoutils.api.routes.initialize_routes") as mock_init_routes,
    ):
        create_app()
        mock_init_routes.assert_not_called()
