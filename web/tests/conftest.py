import datetime
import shutil
import tempfile
import threading
import time
import uuid
import wsgiref
from pathlib import Path

import b3desk.utils
import portpicker
import psycopg
import pytest
from b3desk import create_app
from b3desk.models import db
from flask import Flask
from flask_migrate import Migrate
from flask_webtest import TestApp
from jinja2 import FileSystemBytecodeCache
from joserfc.jwk import RSAKey
from pytest_lazy_fixtures import lf
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import WsgiDAVApp

b3desk.utils.secret_key = lambda: "AZERTY"


def pytest_addoption(parser):
    """Add --db command-line option to pytest."""
    parser.addoption(
        "--db",
        action="append",
        default=[],
        help="database to test (sqlite, postgresql)",
    )


def pytest_generate_tests(metafunc):
    """Parametrize tests with db fixture based on --db option."""
    dbs = metafunc.config.getoption("db") or ["sqlite", "postgresql"]

    if "db" in metafunc.fixturenames:
        fixture_names = [f"{db}_db" for db in dbs]
        metafunc.parametrize("db", [lf(name) for name in fixture_names], ids=dbs)


@pytest.fixture(scope="session")
def sqlite_template_db(tmp_path_factory):
    """Create a SQLite template database with schema."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        template_db_path = f.name

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{template_db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        Migrate(app, db, compare_type=True)
        db.create_all()

    yield Path(template_db_path)

    Path(template_db_path).unlink(missing_ok=True)


@pytest.fixture
def sqlite_db(sqlite_template_db):
    """Create a fresh SQLite database by copying the template."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        test_db_path = f.name

    shutil.copy2(sqlite_template_db, test_db_path)

    yield f"sqlite:///{test_db_path}"

    Path(test_db_path).unlink(missing_ok=True)


@pytest.fixture(scope="session")
def postgresql_template_db(postgresql_proc):
    """Create a PostgreSQL template database with schema."""
    pytest.importorskip("pytest_postgresql")

    proc_info = postgresql_proc
    template_dbname = "b3desk_template"

    conn = psycopg.connect(
        host=proc_info.host,
        port=proc_info.port,
        user=proc_info.user,
        dbname="postgres",
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(f'DROP DATABASE IF EXISTS "{template_dbname}"')
    cursor.execute(f'CREATE DATABASE "{template_dbname}"')
    cursor.close()
    conn.close()

    uri = f"postgresql://{proc_info.user}@{proc_info.host}:{proc_info.port}/{template_dbname}"

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        Migrate(app, db, compare_type=True)
        db.create_all()
        db.session.remove()
        db.engine.dispose()

    yield template_dbname

    conn = psycopg.connect(
        host=proc_info.host,
        port=proc_info.port,
        user=proc_info.user,
        dbname="postgres",
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{template_dbname}'
        AND pid <> pg_backend_pid()
        """
    )
    cursor.execute(f'DROP DATABASE IF EXISTS "{template_dbname}"')
    cursor.close()
    conn.close()


@pytest.fixture
def postgresql_db(postgresql_proc, postgresql_template_db):
    """Create a fresh PostgreSQL database by cloning the template."""
    pytest.importorskip("pytest_postgresql")

    proc_info = postgresql_proc
    test_dbname = f"b3desk_test_{uuid.uuid4().hex[:8]}"

    conn = psycopg.connect(
        host=proc_info.host,
        port=proc_info.port,
        user=proc_info.user,
        dbname="postgres",
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(
        f'CREATE DATABASE "{test_dbname}" TEMPLATE "{postgresql_template_db}"'
    )
    cursor.close()
    conn.close()

    uri = (
        f"postgresql://{proc_info.user}@{proc_info.host}:{proc_info.port}/{test_dbname}"
    )

    yield uri

    conn = psycopg.connect(
        host=proc_info.host,
        port=proc_info.port,
        user=proc_info.user,
        dbname="postgres",
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{test_dbname}'
        AND pid <> pg_backend_pid()
        """
    )
    cursor.execute(f'DROP DATABASE IF EXISTS "{test_dbname}"')
    cursor.close()
    conn.close()


@pytest.fixture
def iam_user(iam_server):
    iam_user = iam_server.random_user(
        id="user_id",
        emails=["alice@domain.tld"],
        given_name="Alice",
        user_name="Alice_user_name",
        family_name="Cooper",
        preferred_username="alice",
    )
    iam_server.backend.save(iam_user)

    yield iam_user
    iam_server.backend.delete(iam_user)


@pytest.fixture
def iam_user_2(iam_server):
    iam_user_2 = iam_server.random_user(
        id="user_id2",
        emails=["berenice@domain.tld"],
        given_name="Berenice",
        user_name="Berenice_user_name",
        family_name="Cooler",
    )
    iam_server.backend.save(iam_user_2)

    yield iam_user_2
    iam_server.backend.delete(iam_user_2)


@pytest.fixture
def iam_client(iam_server):
    iam_client = iam_server.models.Client(
        client_id="client_id",
        client_secret="client_secret",
        redirect_uris=["http://b3desk.test/oidc_callback"],
        token_endpoint_auth_method="client_secret_post",
        post_logout_redirect_uris=["http://b3desk.test/logout"],
        grant_types=["authorization_code"],
        response_types=["code", "token", "id_token"],
        scope=["openid", "profile", "email"],
        preconsent=True,
    )
    iam_server.backend.save(iam_client)
    iam_client.audience = [iam_client]
    iam_server.backend.save(iam_client)
    yield iam_client
    iam_server.backend.delete(iam_client)


@pytest.fixture
def iam_token(iam_server, iam_client, iam_user):
    iam_token = iam_server.random_token(
        client=iam_client,
        subject=iam_user,
    )
    iam_server.backend.save(iam_token)
    yield iam_token
    iam_server.backend.delete(iam_token)


@pytest.fixture(scope="session")
def private_key():
    private_key = RSAKey.generate_key(1024, parameters={"alg": "RS256", "use": "sig"})
    private_pem_bytes = private_key.as_pem(private=True)
    private_pem_str = private_pem_bytes.decode("utf-8")
    return private_pem_str


@pytest.fixture
def configuration(tmp_path, iam_server, iam_client, request, private_key, db):
    configuration = {
        "SECRET_KEY": "test-secret-key",
        "SERVER_NAME": "b3desk.test",
        "PREFERRED_URL_SCHEME": "http",
        "SQLALCHEMY_DATABASE_URI": db,
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
        "SECONDARY_IDENTITY_PROVIDER_ENABLED": False,
        "UPLOAD_DIR": str(tmp_path),
        "TMP_DOWNLOAD_DIR": str(tmp_path),
        "RECORDING": True,
        "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL": "https://bbb-analytics.test/v1/post_events",
        "MEETING_KEY_WORDING": "seminaire",
        "QUICK_MEETING_LOGOUT_URL": "http://quick-meeting-logout.test/",
        "FORCE_HTTPS_ON_EXTERNAL_URLS": False,
        "NC_LOGIN_API_URL": "http://tokenmock.test:9000/",
        "NC_LOGIN_API_KEY": "MY-TOTALLY-COOL-API-KEY",
        "FILE_SHARING": True,
        # Overwrite the web.env values for tests running in docker
        "STATS_URL": None,
        "CACHE_TYPE": "SimpleCache",
        # Disable cache in unit tests
        "CACHE_DEFAULT_TIMEOUT": 0,
        "BIGBLUEBUTTON_API_CACHE_DURATION": 0,
        "MEETING_LOGOUT_URL": "https://meeting-logout.test/logout",
        "MAIL_MEETING": True,
        "SMTP_FROM": "from@mail.test",
        "BIGBLUEBUTTON_DIALNUMBER": "+33bbbphonenumber",
        "ENABLE_PIN_MANAGEMENT": True,
        "ENABLE_SIP": True,
        "FQDN_SIP_SERVER": "sip.test",
        "PRIVATE_KEY": private_key,
        "PISTE_OAUTH_CLIENT_ID": "client-id",
        "PISTE_OAUTH_CLIENT_SECRET": "client-secret",
    }

    if "smtpd" in request.fixturenames:
        smtpd = request.getfixturevalue("smtpd")
        smtpd.config.use_starttls = True
        configuration["SMTP_HOST"] = smtpd.hostname
        configuration["SMTP_PORT"] = smtpd.port
        configuration["SMTP_SSL"] = smtpd.config.use_ssl
        configuration["SMTP_STARTTLS"] = smtpd.config.use_starttls
        configuration["SMTP_USERNAME"] = smtpd.config.login_username
        configuration["SMTP_PASSWORD"] = smtpd.config.login_password

    return configuration


@pytest.fixture(scope="session")
def jinja_cache_directory(tmp_path_factory):
    return tmp_path_factory.mktemp("cache")


@pytest.fixture
def app(configuration, jinja_cache_directory):
    app = create_app(configuration)
    app.jinja_env.bytecode_cache = FileSystemBytecodeCache(jinja_cache_directory)

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
    from b3desk.models.meetings import Meeting

    meeting = Meeting(
        user=user,
        name="meeting",
        maxParticipants=99,
        duration=999,
        moderatorPW="moderator",
        attendeePW="attendee",
        is_favorite=True,
        voiceBridge="111111111",
        last_connection_utc_datetime=datetime.datetime(2023, 1, 1),
        visio_code="911111111",
    )
    meeting.save()

    yield meeting


@pytest.fixture
def meeting_2(client_app, user):
    from b3desk.models.meetings import Meeting

    meeting = Meeting(
        user=user,
        name="a meeting",
        maxParticipants=99,
        duration=999,
        moderatorPW="moderator",
        attendeePW="attendee",
        is_favorite=True,
        voiceBridge="111111112",
        last_connection_utc_datetime=datetime.datetime(2024, 1, 1),
        visio_code="911111112",
    )
    meeting.save()

    yield meeting


@pytest.fixture
def meeting_3(client_app, user):
    from b3desk.models.meetings import Meeting

    meeting = Meeting(
        user=user,
        name="meeting",
        maxParticipants=99,
        duration=999,
        moderatorPW="moderator",
        attendeePW="attendee",
        voiceBridge="111111113",
        visio_code="911111113",
    )
    meeting.save()

    yield meeting


@pytest.fixture
def shadow_meeting(client_app, user):
    from b3desk.models.meetings import Meeting

    meeting = Meeting(
        user=user,
        name="shadow meeting",
        moderatorPW="moderator",
        attendeePW="attendee",
        voiceBridge="555555551",
        is_shadow=True,
        last_connection_utc_datetime=datetime.datetime(2025, 1, 1),
        visio_code="511111111",
    )
    meeting.save()

    yield meeting


@pytest.fixture
def shadow_meeting_2(client_app, user):
    from b3desk.models.meetings import Meeting

    meeting = Meeting(
        user=user,
        name="shadow meeting must disappear",
        moderatorPW="moderator",
        attendeePW="attendee",
        voiceBridge="555555552",
        is_shadow=True,
        last_connection_utc_datetime=datetime.datetime(2020, 1, 1),
        visio_code="511111112",
    )
    meeting.save()

    yield meeting


@pytest.fixture
def shadow_meeting_3(client_app, user):
    from b3desk.models.meetings import Meeting

    meeting = Meeting(
        user=user,
        name="shadow meeting must disappear too",
        moderatorPW="moderator",
        attendeePW="attendee",
        voiceBridge="555555553",
        is_shadow=True,
        last_connection_utc_datetime=datetime.datetime(2024, 1, 1),
        visio_code="511111113",
    )
    meeting.save()

    yield meeting


@pytest.fixture
def user(client_app, iam_user):
    from b3desk.models.users import User

    user = User(
        email=iam_user.emails[0],
        given_name=iam_user.given_name,
        family_name=iam_user.family_name,
        preferred_username=iam_user.preferred_username,
    )
    user.save()

    yield user


@pytest.fixture
def user_2(client_app, iam_user_2):
    from b3desk.models.users import User

    user_2 = User(
        email=iam_user_2.emails[0],
        given_name=iam_user_2.given_name,
        family_name=iam_user_2.family_name,
    )
    user_2.save()

    yield user_2


@pytest.fixture
def previous_voiceBridge(client_app):
    from b3desk.models.meetings import PreviousVoiceBridge

    previous_voiceBridge = PreviousVoiceBridge(voiceBridge="487604786")
    previous_voiceBridge.save()

    yield previous_voiceBridge


@pytest.fixture
def authenticated_user(client_app, user, iam_token, iam_server, iam_user):
    with client_app.session_transaction() as session:
        session["access_token"] = iam_token.access_token
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
        session["refresh_token"] = ("",)
        session["visio_code_attempt_counter"] = 0

    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    yield user


@pytest.fixture
def authenticated_user_2(client_app, user_2, iam_token, iam_server, iam_user_2):
    with client_app.session_transaction() as session:
        session["access_token"] = iam_token.access_token
        session["access_token_expires_at"] = ""
        session["current_provider"] = "default"
        session["id_token"] = ""
        session["id_token_jwt"] = ""
        session["last_authenticated"] = "true"
        session["last_session_refresh"] = time.time()
        session["userinfo"] = {
            "email": "berenice@domain.tld",
            "family_name": "Cooler",
            "given_name": "Berenice",
            "preferred_username": "berenice",
        }
        session["refresh_token"] = ""

    iam_server.login(iam_user_2)
    iam_server.consent(iam_user_2)

    yield user_2


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
    class Response:
        content = """<response><returncode>SUCCESS</returncode><running>true</running></response>"""
        status_code = 200
        text = ""

    yield mocker.patch("requests.Session.send", return_value=Response)


@pytest.fixture(scope="session")
def webdav_server(tmp_path_factory):
    root_path = Path(tmp_path_factory.mktemp("webdav"))
    (root_path / "remote.php" / "dav" / "files" / "alice").mkdir(
        parents=True, exist_ok=True
    )
    provider = FilesystemProvider(root_path, readonly=False, fs_opts={})

    config = {
        "host": "localhost",
        "port": portpicker.pick_unused_port(),
        "provider_mapping": {"/": provider},
        "http_authenticator": {"domain_controller": None},
        "simple_dc": {"user_mapping": {"*": True}},
        "verbose": 4,
        "logging": {
            "enable": True,
            "enable_loggers": [],
        },
    }
    app = WsgiDAVApp(config)

    server = wsgiref.simple_server.make_server("localhost", config["port"], app)

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    try:
        yield app
    finally:
        server.shutdown()
        server_thread.join()


class CloudTokenResponse:
    def __init__(self, nc_locator):
        self.data = {
            "nctoken": str(uuid.uuid4()),
            "nclocator": nc_locator,
            "nclogin": "alice",
        }

    def json(self):
        return self.data


@pytest.fixture(autouse=True)
def nextcloud_credentials(mocker, webdav_server):
    response = CloudTokenResponse(
        nc_locator=f"http://{webdav_server.config['host']}:{webdav_server.config['port']}",
    ).data
    mocker.patch(
        "b3desk.nextcloud.make_nextcloud_credentials_request", return_value=response
    )
    return response


@pytest.fixture
def cloud_service_response(mocker, webdav_server, request):
    scheme = "http://"
    if "secure" in request.keywords:
        scheme = "https://"
    elif "no_scheme" in request.keywords:
        scheme = ""
    return CloudTokenResponse(nc_locator=f"{scheme}cloud-auth-serv.ice")


@pytest.fixture
def jpg_file_content():
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc2\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?\x10"


class ValidToken:
    def raise_for_status():
        pass

    def json():
        return {"access_token": "valid_token"}


@pytest.fixture
def valid_secondary_identity_token(mocker):
    mocker.patch(
        "b3desk.nextcloud.get_secondary_identity_provider_token",
        return_value=ValidToken,
    )
