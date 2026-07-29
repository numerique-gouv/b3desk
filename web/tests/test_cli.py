from b3desk.commands import bp
from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.users import User


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
    assert db.session.query(User).count() == 5
    assert db.session.query(Meeting).count() == 8
    assert db.session.query(Group).count() == 5


def test_populate_without_users(cli_runner, client_app):
    """Test CLI populate creates no meeting and no group when asked for zero user."""
    res = cli_runner.invoke(bp.cli, ["populate", "--users", "0", "--meetings", "5"])
    assert res.exit_code == 0, res.output
    assert db.session.query(User).count() == 0
    assert db.session.query(Meeting).count() == 0
    assert db.session.query(Group).count() == 0


def test_populate_refuses_outside_development(cli_runner, client_app, app, monkeypatch):
    """Test CLI populate is unavailable when neither debug nor testing is on."""
    monkeypatch.setattr(app, "debug", False)
    monkeypatch.setattr(app, "testing", False)
    res = cli_runner.invoke(bp.cli, ["populate", "--users", "1", "--meetings", "1"])
    assert res.exit_code != 0
    assert "only available in development" in res.output
    assert db.session.query(User).count() == 0
