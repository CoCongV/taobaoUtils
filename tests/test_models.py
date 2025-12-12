from datetime import UTC, datetime, timedelta

from taobaoutils.models import APIToken, ProductListing, RequestConfig, User


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

    d = u.to_dict()
    assert d["username"] == "testuser"


def test_product_listing_model(session):
    u = User(username="user", email="u@e.com", password="pwd")
    session.add(u)
    session.commit()

    rc = RequestConfig(user_id=u.id, name="Config 1", body={}, header={})
    session.add(rc)
    session.commit()

    pl = ProductListing(user_id=u.id, request_config_id=rc.id, product_link="http://test.com", product_id="123")
    session.add(pl)
    session.commit()

    assert pl.id is not None
    assert pl.status == "pending"
    assert pl.request_config_id == rc.id
    assert str(pl) == "<ProductListing 1 - 123>"

    d = pl.to_dict()
    assert d["product_link"] == "http://test.com"
    assert d["status"] == "pending"
    assert d["request_config_id"] == rc.id


def test_request_config_model(session):
    u = User(username="user", email="u@e.com", password="pwd")
    session.add(u)
    session.commit()

    rc = RequestConfig(user_id=u.id, name="Test Config", body={"u": "{product_link}"}, header={})
    session.add(rc)
    session.commit()

    assert rc.id is not None
    assert rc.method == "POST"
    assert str(rc) == "<RequestConfig 1 - Test Config>"

    # Test custom method
    rc2 = RequestConfig(user_id=u.id, name="Config 2", body={}, header={}, method="GET")
    session.add(rc2)
    session.commit()
    assert rc2.method == "GET"

    # Test to_dict
    d = rc.to_dict()
    assert d["method"] == "POST"

    # Test generate_body
    class MockProduct:
        def to_dict(self):
            return {"product_link": "http://test.com", "title": "Title"}

    generated = rc.generate_body(MockProduct())
    assert generated == {"u": "http://test.com"}


def test_api_token_model(session):
    u = User(username="user", email="u@e.com", password="pwd")
    session.add(u)
    session.commit()

    token_str, token = APIToken.create_token(u.id, "My Token", scopes=["read"], expires_days=7)
    session.add(token)
    session.commit()

    assert token.id is not None
    assert token.verify_token(token_str)
    assert not token.verify_token("wrong")
    assert token.get_scopes() == ["read"]
    assert token.token == token_str  # Verify plaintext storage

    d = token.to_dict()
    assert d["name"] == "My Token"
    assert d["display_token"].startswith(token.prefix)

    # Test expiration
    token.expires_at = datetime.now(UTC) - timedelta(days=1)
    assert not token.verify_token(token_str)
