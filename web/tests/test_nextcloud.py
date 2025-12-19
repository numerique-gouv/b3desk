from b3desk.models import db
from b3desk.nextcloud import check_nextcloud_connection
from webdav3.exceptions import NoConnection
from webdav3.exceptions import WebDavException


def test_check_connection_success(client_app, user, mocker):
    """Connection check passes when WebDAV list succeeds."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list")

    result = check_nextcloud_connection(user)

    assert result is True


def test_check_connection_missing_credentials(client_app, user, mocker):
    """Connection check fails when credentials are missing."""
    user.nc_login = None
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    result = check_nextcloud_connection(user)

    assert result is False


def test_check_connection_webdav_error(client_app, user, mocker):
    """Connection check fails on WebDAV error."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list", side_effect=WebDavException)

    result = check_nextcloud_connection(user)

    assert result is False


def test_check_connection_marks_unavailable_on_connection_error(
    app, client_app, user, mocker
):
    """Connection check marks Nextcloud unavailable on connection error."""
    from b3desk import cache

    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch(
        "webdav3.client.Client.list", side_effect=NoConnection("nextcloud.test")
    )

    result = check_nextcloud_connection(user)

    assert result is False
    with app.app_context():
        assert cache.get(f"nc_unavailable:{user.nc_locator}") is True


def test_check_connection_retry_refreshes_credentials(client_app, user, mocker):
    """Connection check with retry_on_wrong_credentials refreshes credentials on failure."""
    user.nc_login = None
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    update_mock = mocker.patch(
        "b3desk.nextcloud.update_user_nc_credentials", return_value=True
    )
    mocker.patch("webdav3.client.Client.list")

    def set_credentials(user, force_renew=False):
        user.nc_login = "alice"
        return True

    update_mock.side_effect = set_credentials

    result = check_nextcloud_connection(user, retry_on_wrong_credentials=True)

    assert result is True
    update_mock.assert_called_once_with(user, force_renew=True)


def test_check_connection_no_retry_by_default(client_app, user, mocker):
    """Connection check does not retry by default."""
    user.nc_login = None
    db.session.add(user)
    db.session.commit()

    update_mock = mocker.patch("b3desk.nextcloud.update_user_nc_credentials")

    result = check_nextcloud_connection(user)

    assert result is False
    update_mock.assert_not_called()
