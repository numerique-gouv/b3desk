import time

import b3desk.utils
import pytest
from b3desk import create_app
from flask_migrate import Migrate
from flask_webtest import TestApp

b3desk.utils.secret_key = lambda: "AZERTY"
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.users import User


@pytest.fixture
def iam_client(iam_server):
    iam_client = iam_server.models.Client(
        client_id="client_id",
        client_secret="client_secret",
        redirect_uris=["http://localhost:5000/oidc_callback"],
        token_endpoint_auth_method="client_secret_post",
        post_logout_redirect_uris=["http://localhost:5000/logout"],
        grant_types=["authorization_code"],
        response_types=["code", "token", "id_token"],
        scope=["openid", "profile", "email"],
        preconsent=True,
    )
    iam_client.audience = [iam_client]
    iam_client.save()
    yield iam_client
    iam_client.delete()


@pytest.fixture
def configuration(tmp_path, iam_server, iam_client):
    return {
        "SECRET_KEY": "test-secret-key",
        "SERVER_FQDN": "http://localhost:5000",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "TESTING": True,
        "BIGBLUEBUTTON_ENDPOINT": "https://bbb.test",
        "OIDC_ISSUER": iam_server.url,
        "OIDC_REDIRECT_URI": iam_client.redirect_uris[0],
        "OIDC_CLIENT_ID": iam_client.client_id,
        "OIDC_CLIENT_SECRET": iam_client.client_secret,
        "OIDC_CLIENT_AUTH_METHOD": iam_client.token_endpoint_auth_method,
        "OIDC_SCOPES": iam_client.scope,
        "OIDC_USERINFO_HTTP_METHOD": "GET",
        "UPLOAD_DIR": str(tmp_path),
        "TMP_DOWNLOAD_DIR": str(tmp_path),
        "RECORDING": True,
        "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
        "MEETING_KEY_WORDING": "seminaire",
        "QUICK_MEETING_LOGOUT_URL": "http://education.gouv.fr/",
    }


@pytest.fixture
def app(configuration):
    app = create_app(configuration)
    with app.app_context():
        Migrate(app, db, compare_type=True)
        db.create_all()

    return app


@pytest.fixture
def client_app(app):
    with app.test_request_context():
        yield TestApp(app)


@pytest.fixture
def meeting(client_app, user):
    meeting = Meeting(user=user)
    meeting.save()

    yield meeting


@pytest.fixture
def user(client_app):
    user = User(email="alice@domain.tld", given_name="Alice", family_name="Cooper")
    user.save()

    yield user


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def bbb_response(mocker):
    class Resp:
        content = """<response><returncode>SUCCESS</returncode><running>true</running></response>"""
        status_code = 200

    mocker.patch("requests.get", return_value=Resp)
