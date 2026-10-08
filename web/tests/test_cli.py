import pathlib

import pytest
from b3desk.commands import bp
from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.users import User
from b3desk.settings import MainSettings
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
def config_dump_app(monkeypatch):
    """Build a minimal app with a fixed configuration for config-dump tests."""
    # Ignore any environment variable that could alter the settings on the dev machine
    for name in MainSettings.model_fields:
        monkeypatch.delenv(name, raising=False)

    settings = MainSettings(
        SECRET_KEY="test-secret-key",
        SERVER_NAME="b3desk.test",
        PREFERRED_URL_SCHEME="http",
        SQLALCHEMY_DATABASE_URI="postgresql://user:password@postgres/b3desk",
        UPLOAD_DIR="/tmp/b3desk/upload",
        TMP_DOWNLOAD_DIR="/tmp/b3desk/download",
        BIGBLUEBUTTON_ENDPOINT="https://bbb.test",
        BIGBLUEBUTTON_SECRET="test-bbb-secret",
        OIDC_ISSUER="https://iam.test",
        OIDC_CLIENT_ID="test-client-id",
        OIDC_CLIENT_SECRET="test-client-secret",
    )
    app = Flask(__name__)
    app.config.from_object(settings)
    Babel(app)
    return app


def test_config_dump(config_dump_app, tmp_path, monkeypatch):
    """Export a fixed configuration and compare it with the reference dotenv file."""
    monkeypatch.chdir(tmp_path)
    with config_dump_app.app_context():
        res = config_dump_app.test_cli_runner(catch_exceptions=False).invoke(
            bp.cli, ["config-dump"]
        )
    assert res.exit_code == 0, res.output

    exported_config = (tmp_path / "web.env.dump").read_text()
    expected_config = (
        pathlib.Path(__file__).parent / "fixtures" / "web.env.test"
    ).read_text()
    assert exported_config == expected_config


def test_config_dump_output(config_dump_app, tmp_path):
    """Export the configuration to a custom location."""
    output = tmp_path / "subdir" / "custom.env"
    with config_dump_app.app_context():
        res = config_dump_app.test_cli_runner(catch_exceptions=False).invoke(
            bp.cli, ["config-dump", "--output", str(output)]
        )
    assert res.exit_code == 0, res.output

    expected_config = (
        pathlib.Path(__file__).parent / "fixtures" / "web.env.test"
    ).read_text()
    assert output.read_text() == expected_config
