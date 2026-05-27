from b3desk.commands import bp


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
