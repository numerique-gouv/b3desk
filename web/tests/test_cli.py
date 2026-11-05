import pathlib

import pytest
from b3desk import setup_configuration
from b3desk.commands import bp
from b3desk.commands import dotenv_quote
from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.users import User
from b3desk.settings import MainSettings
from dotenv import dotenv_values
from flask import Flask
from flask_babel import Babel


def test_get_apps_id(cli_runner, user):
    """Test CLI get-apps-id."""
    res = cli_runner.invoke(bp.cli, ["get-apps-id", "alice@domain.tld"])
    assert res.exit_code == 0, res.output


def test_user_to_admin(cli_runner, user):
    """Test CLI user-to-admin."""
    res = cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    assert res.output_bytes == b"User to Admin result: Alice Cooper is admin.\n"


def test_admin_to_user(cli_runner, user):
    """Test CLI admin-to-user."""
    res = cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = cli_runner.invoke(bp.cli, ["admin-to-user", "alice@domain.tld"])
    assert res.output_bytes == b"Admin to User result: Alice Cooper is not admin.\n"


def test_user_to_admin_with_wrong_email(cli_runner, user):
    """Test CLI user-to-admin with a wrong email."""
    res = cli_runner.invoke(bp.cli, ["user-to-admin", "wrong_email@domain.tld"])
    assert (
        res.output_bytes
        == b"User to Admin result: No user with this email was found.\n"
    )


def test_admin_to_user_with_wrong_email(cli_runner, user):
    """Test CLI admin-to-user with a wrong email."""
    res = cli_runner.invoke(bp.cli, ["admin-to-user", "wrong_email@domain.tld"])
    assert (
        res.output_bytes
        == b"Admin to User result: No user with this email was found.\n"
    )


def test_populate(cli_runner, client_app):
    """Test CLI populate generates the requested amount of data."""
    res = cli_runner.invoke(
        bp.cli, ["populate", "--users", "5", "--meetings", "8", "--seed", "42"]
    )
    assert res.exit_code == 0, res.output
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 5
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 8
    assert db.session.scalar(db.select(db.func.count()).select_from(Group)) == 5


def test_populate_without_users(cli_runner, client_app):
    """Test CLI populate creates no meeting and no group when asked for zero user."""
    res = cli_runner.invoke(bp.cli, ["populate", "--users", "0", "--meetings", "5"])
    assert res.exit_code == 0, res.output
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 0
    assert db.session.scalar(db.select(db.func.count()).select_from(Group)) == 0


def test_populate_refuses_outside_development(cli_runner, client_app, app, monkeypatch):
    """Test CLI populate is unavailable when neither debug nor testing is on."""
    monkeypatch.setattr(app, "debug", False)
    monkeypatch.setattr(app, "testing", False)
    res = cli_runner.invoke(bp.cli, ["populate", "--users", "1", "--meetings", "1"])
    assert res.exit_code != 0
    assert "only available in development" in res.output
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0


@pytest.fixture
def config_dump_config(monkeypatch):
    """Return a minimal fixed configuration for config-dump tests."""
    # Ignore any environment variable that could alter the settings on the dev machine
    for name in MainSettings.model_fields:
        monkeypatch.delenv(name, raising=False)

    return {
        "SECRET_KEY": "test-secret-key",
        "SERVER_NAME": "b3desk.test",
        "PREFERRED_URL_SCHEME": "http",
        "SESSION_COOKIE_NAME": "session",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:password@postgres/b3desk",
        "UPLOAD_DIR": "/tmp/b3desk/upload",
        "TMP_DOWNLOAD_DIR": "/tmp/b3desk/download",
        "BIGBLUEBUTTON_ENDPOINT": "https://bbb.test",
        "BIGBLUEBUTTON_SECRET": "test-bbb-secret",
        "OIDC_ISSUER": "https://iam.test",
        "OIDC_CLIENT_ID": "test-client-id",
        "OIDC_CLIENT_SECRET": "test-client-secret",
    }


def make_config_dump_app(config):
    """Build a minimal app configured like the real one."""
    app = Flask(__name__)
    setup_configuration(app, config)
    Babel(app)
    return app


def dump_config(app, output=None):
    """Run config-dump and return the path of the exported file."""
    args = ["config-dump"]
    if output:
        args += ["--output", str(output)]
    with app.app_context():
        res = app.test_cli_runner(catch_exceptions=False).invoke(bp.cli, args)
    assert res.exit_code == 0, res.output
    return pathlib.Path(output or "web.env.dump")


@pytest.mark.parametrize("output", [None, "subdir/custom.env"])
def test_config_dump(config_dump_config, tmp_path, monkeypatch, output):
    """Export a fixed configuration and compare it with the reference dotenv file."""
    monkeypatch.chdir(tmp_path)
    app = make_config_dump_app(config_dump_config)
    exported_file = dump_config(app, output)

    assert exported_file.stat().st_mode & 0o777 == 0o600
    expected_config = (
        pathlib.Path(__file__).parent / "fixtures" / "web.env.test"
    ).read_text()
    assert exported_file.read_text() == expected_config


def test_config_dump_reload(config_dump_config, tmp_path, monkeypatch):
    """Load the exported file back and get the same settings."""
    log_config = tmp_path / "logging.toml"
    log_config.write_text("version = 1\n")
    config = {
        **config_dump_config,
        "SERVICE_TITLE": 'Webinaire de l’État "test"',
        "OIDC_SCOPES": ["openid", "email", "usual_name"],
        "RIE_NETWORK_IPS": ["10.0.0.0/8", "192.168.0.0/16"],
        "ALLOWED_MIME_TYPES_SERVER_SIDE": ["application/pdf", "image/png"],
        "OIDC_CLAIMS_MAPPING": {"family_name": "usual_name"},
        "VIDEO_STREAMING_LINKS": {"Vidéo l'État": "https://video.test/a"},
        "RECORDING_DURATION": "P30D",
        "RECORDING_EXPECTED_FORMATS": [],
        "BIGBLUEBUTTON_SECRET": "pa$$word${HOME}",
        "PRIVATE_KEY": "-----BEGIN KEY-----\nabc\n-----END KEY-----",
        "MAX_MEETINGS_PER_USER": 3,
        "FILE_SHARING": True,
        "LOG_CONFIG": str(log_config),
    }
    app = make_config_dump_app(config)
    output = tmp_path / "web.env.dump"
    dump_config(app, output)

    for name, value in dotenv_values(output, interpolate=False).items():
        monkeypatch.setenv(name, value)
    with app.app_context():
        reloaded = MainSettings()
        assert reloaded.model_dump() == MainSettings(**config).model_dump()
        assert reloaded.model_fields_set == MainSettings(**config).model_fields_set


@pytest.mark.parametrize(
    "value,expected",
    [
        ("pa$word${HOME}", "'pa$word${HOME}'"),
        ("it's", "'it\\'s'"),
        ("a\\b", "'a\\b'"),
        ('"q"\nl2', "'\"q\"\nl2'"),
    ],
)
def test_dotenv_quote(value, expected):
    """Docker Compose reads single-quoted values as is, except for escaped quotes."""
    assert dotenv_quote(value) == expected


def test_config_dump_comments_computed_values(config_dump_config, tmp_path):
    """Values computed from other settings are not exported as explicit settings."""
    config = {**config_dump_config, "PREFERRED_URL_SCHEME": "https"}
    app = make_config_dump_app(config)
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["OIDC_ATTENDEE_CLIENT_SECRET"] == "test-client-secret"

    exported_config = (
        dump_config(app, tmp_path / "web.env.dump").read_text().splitlines()
    )

    assert "# SESSION_COOKIE_SECURE=" in exported_config
    assert "# OIDC_ATTENDEE_CLIENT_SECRET=" in exported_config
    assert not any(
        line.startswith(("SESSION_COOKIE_SECURE=", "OIDC_ATTENDEE_"))
        for line in exported_config
    )


def test_config_dump_comments_empty_attendee_settings(
    config_dump_config, tmp_path, monkeypatch
):
    """Empty attendee settings follow the main OIDC settings and stay commented."""
    for name in (
        "OIDC_ATTENDEE_ISSUER",
        "OIDC_ATTENDEE_CLIENT_ID",
        "OIDC_ATTENDEE_CLIENT_SECRET",
        "OIDC_ATTENDEE_CLIENT_AUTH_METHOD",
        "OIDC_ATTENDEE_SCOPES",
    ):
        monkeypatch.setenv(name, "")
    app = make_config_dump_app(config_dump_config)
    assert app.config["OIDC_ATTENDEE_CLIENT_SECRET"] == "test-client-secret"
    assert app.config["OIDC_ATTENDEE_SCOPES"] == ["openid", "email", "profile"]

    exported_config = (
        dump_config(app, tmp_path / "web.env.dump").read_text().splitlines()
    )

    assert not any(line.startswith("OIDC_ATTENDEE_") for line in exported_config)


def test_user_to_admin_with_admin_management_disabled(cli_runner, client_app, user):
    """Test CLI user-to-admin grants admin rights when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    res = cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    assert res.exit_code == 0
    assert "Admin management is disabled." in res.output
    db.session.refresh(user)
    assert user.admin
    assert not user.has_admin_rights
