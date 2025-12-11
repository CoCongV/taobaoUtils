from datetime import datetime, timedelta

import pytest

from taobaoutils.app import create_app, db
from taobaoutils.models import APIToken, ProductListing, RequestConfig, User


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session


def test_user_model(session):
    u = User(username="testuser", email="test@example.com", password="password123")
    session.add(u)
    session.commit()

    assert u.id is not None
    assert u.verify_password("password123")
    assert not u.verify_password("wrong")
    assert str(u) == "<User testuser>"
    assert u.identity == u.id
    assert u.rolenames == ["user"]

    u.set_token("token123")
    assert u.taobao_token == "token123"

    d = u.to_dict()
    assert d["username"] == "testuser"
    assert d["taobao_token"] is True


def test_product_listing_model(session):
    u = User(username="user", email="u@e.com", password="pwd")
    session.add(u)
    session.commit()

    pl = ProductListing(user_id=u.id, product_link="http://test.com", product_id="123")
    session.add(pl)
    session.commit()

    assert pl.id is not None
    assert pl.status == "requested"
    assert str(pl) == "<ProductListing 1 - 123>"

    d = pl.to_dict()
    assert d["product_link"] == "http://test.com"
    assert d["status"] == "requested"


def test_request_config_model(session):
    u = User(username="user", email="u@e.com", password="pwd")
    session.add(u)
    session.commit()

    rc = RequestConfig(user_id=u.id, name="Test Config")
    session.add(rc)
    session.commit()

    assert rc.id is not None
    assert str(rc) == "<RequestConfig 1 - Test Config>"

    # Test cookie setting
    rc.set_cookie({"a": 1, "b": 2})
    assert "Cookie" in rc.header
    assert "a=1" in rc.header

    d = rc.to_dict()
    assert d["name"] == "Test Config"
    assert d["header"]["Cookie"] == "a=1; b=2"


def test_api_token_model(session):
    u = User(username="user", email="u@e.com", password="pwd")
    session.add(u)
    session.commit()

    token_str, token = APIToken.generate_token(u.id, "My Token", scopes=["read"], expires_days=7)
    session.add(token)
    session.commit()

    assert token.id is not None
    assert token.verify_token(token_str)
    assert not token.verify_token("wrong")
    assert token.get_scopes() == ["read"]

    d = token.to_dict()
    assert d["name"] == "My Token"
    assert d["display_token"].startswith(token.prefix)

    # Test expiration
    token.expires_at = datetime.utcnow() - timedelta(days=1)
    assert not token.verify_token(token_str)
