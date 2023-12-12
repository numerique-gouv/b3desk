import functools
import time

import b3desk.utils
import pytest
from b3desk import create_app
from flask_migrate import Migrate
from flask_webtest import TestApp


b3desk.utils.secret_key = lambda: "AZERTY"

from b3desk.models import db
from b3desk.models.users import User
from b3desk.models.meetings import Meeting


class FakeAuth:
    def token_auth(self, provider_name):
        def token_decorator(view_func):
            @functools.wraps(view_func)
            def wrapper(*args, **kwargs):
                return view_func(*args, **kwargs)

            return wrapper

        return token_decorator

    def oidc_auth(self, provider_name):
        def token_decorator(view_func):
            @functools.wraps(view_func)
            def wrapper(*args, **kwargs):
                return view_func(*args, **kwargs)

            return wrapper

        return token_decorator

    def oidc_logout(self, view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)

        return wrapper


@pytest.fixture()
def app(mocker, tmp_path):
    mocker.patch("flask_pyoidc.OIDCAuthentication", return_value=FakeAuth())
    app = create_app(
        test_config={
            "SECRET_KEY": "test-secret-key",
            "SERVER_FQDN": "http://localhost:5000",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "TESTING": True,
            "BIGBLUEBUTTON_ENDPOINT": "https://bbb.test",
            "OIDC_ISSUER": "http://oidc-server.test",
            "UPLOAD_DIR": str(tmp_path),
            "TMP_DOWNLOAD_DIR": str(tmp_path),
            "RECORDING": True,
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
            "MEETING_KEY_WORDING": "seminaire",
            "QUICK_MEETING_LOGOUT_URL": "http://education.gouv.fr/",
        }
    )
    with app.app_context():
        Migrate(app, db, compare_type=True)
        db.create_all()

    return app


@pytest.fixture()
def client_app(app):
    return TestApp(app)


@pytest.fixture()
def meeting(app, user):
    meeting = Meeting(user=user)
    meeting.save()

    yield meeting


@pytest.fixture()
def user(app):
    user = User(email="alice@domain.tld", given_name="Alice", family_name="Cooper")
    user.save()

    yield user


@pytest.fixture()
def authenticated_user(client_app, user):
    with client_app.session_transaction() as session:
        session["access_token"] = ""
        session["access_token_expires_at"] = ""
        session["current_provider"] = "default"
        session["id_token"] = ""
        session["id_token_jwt"] = ""
        session["last_authenticated"] = "true"
        session["last_session_refresh"] = time.time()
        session["userinfo"] = {
            "email": "alice@domain.tld",
            "family_name": "Cooper",
            "given_name": "Alice",
            "preferred_username": "alice",
        }
        session["refresh_token"] = ""

    yield user


@pytest.fixture()
def authenticated_attendee(client_app, user, mocker):
    with client_app.session_transaction() as session:
        session["access_token"] = ""
        session["access_token_expires_at"] = ""
        session["current_provider"] = "attendee"
        session["id_token"] = ""
        session["id_token_jwt"] = ""
        session["last_authenticated"] = "true"
        session["last_session_refresh"] = time.time()
        session["userinfo"] = {
            "email": "bob@domain.tld",
            "family_name": "Dylan",
            "given_name": "Bob",
        }
        session["refresh_token"] = ""

    yield user


@pytest.fixture()
def bbb_response(mocker):
    class Resp:
        content = """<response><returncode>SUCCESS</returncode><running>true</running></response>"""
        status_code = 200

    mocker.patch("requests.get", return_value=Resp)
