from b3desk import cache
from b3desk.models import db
from b3desk.nextcloud import check_nextcloud_connection
from b3desk.nextcloud import clear_credentials_fetch_backoff
from b3desk.nextcloud import clear_user_auth_backoff
from b3desk.nextcloud import is_auth_error
from b3desk.nextcloud import is_credentials_fetch_blocked
from b3desk.nextcloud import is_user_auth_blocked
from b3desk.nextcloud import mark_credentials_fetch_failed
from b3desk.nextcloud import mark_user_auth_failed
from b3desk.nextcloud import update_user_nc_credentials
from webdav3.exceptions import NoConnection
from webdav3.exceptions import ResponseErrorCode
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
    """Connection check with retry_on_auth_error refreshes credentials on failure."""
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

    result = check_nextcloud_connection(user, retry_on_auth_error=True)

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


def test_check_connection_no_retry_on_unavailable_error(client_app, user, mocker):
    """Connection check does not retry credentials on unavailability errors."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch(
        "webdav3.client.Client.list", side_effect=NoConnection("nextcloud.test")
    )
    update_mock = mocker.patch("b3desk.nextcloud.update_user_nc_credentials")

    result = check_nextcloud_connection(user, retry_on_auth_error=True)

    assert result is False
    update_mock.assert_not_called()


def test_is_auth_error_detects_401(client_app):
    """is_auth_error returns True for 401 errors."""
    error = ResponseErrorCode("http://test", 401, "Unauthorized")
    assert is_auth_error(error) is True


def test_is_auth_error_detects_403(client_app):
    """is_auth_error returns True for 403 errors."""
    error = ResponseErrorCode("http://test", 403, "Forbidden")
    assert is_auth_error(error) is True


def test_is_auth_error_rejects_500(client_app):
    """is_auth_error returns False for 500 errors."""
    error = ResponseErrorCode("http://test", 500, "Server Error")
    assert is_auth_error(error) is False


def test_is_auth_error_rejects_other_exceptions(client_app):
    """is_auth_error returns False for non-ResponseErrorCode exceptions."""
    error = NoConnection("test")
    assert is_auth_error(error) is False


def test_user_auth_backoff_cycle(app, client_app, user):
    """User auth backoff marks user as blocked then clears."""
    db.session.add(user)
    db.session.commit()

    assert is_user_auth_blocked(user) is False

    mark_user_auth_failed(user)
    assert is_user_auth_blocked(user) is True

    clear_user_auth_backoff(user)
    assert is_user_auth_blocked(user) is False


def test_check_connection_skips_when_user_auth_blocked(client_app, user, mocker):
    """Connection check returns False immediately when user is blocked."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mark_user_auth_failed(user)

    list_mock = mocker.patch("webdav3.client.Client.list")

    result = check_nextcloud_connection(user)

    assert result is False
    list_mock.assert_not_called()


def test_check_connection_marks_user_on_auth_error_after_retry(
    app, client_app, user, mocker
):
    """Connection check marks user as auth failed after retry fails with 401."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch(
        "webdav3.client.Client.list",
        side_effect=ResponseErrorCode("http://test", 401, "Unauthorized"),
    )
    mocker.patch("b3desk.nextcloud.update_user_nc_credentials", return_value=True)

    result = check_nextcloud_connection(user, retry_on_auth_error=True)

    assert result is False
    with app.app_context():
        assert cache.get(f"nc_auth_failed:{user.id}") is True


def test_check_connection_clears_backoff_on_success(app, client_app, user, mocker):
    """Connection check clears user auth backoff on success."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mark_user_auth_failed(user)
    assert is_user_auth_blocked(user) is True

    mocker.patch("webdav3.client.Client.list")

    clear_user_auth_backoff(user)

    result = check_nextcloud_connection(user)

    assert result is True
    with app.app_context():
        assert cache.get(f"nc_auth_failed:{user.id}") is None


def test_update_credentials_marks_blocked_on_failure(app, client_app, user, mocker):
    """Credentials fetch failure marks user in backoff."""
    user.nc_login = None
    user.nc_locator = None
    user.nc_token = None
    user.nc_last_auto_enroll = None
    db.session.add(user)
    db.session.commit()

    mocker.patch(
        "b3desk.nextcloud.get_user_nc_credentials",
        return_value={"error": "connection failed", "nclogin": "test"},
    )

    result = update_user_nc_credentials(user)

    assert result is False
    assert is_credentials_fetch_blocked(user) is True


def test_update_credentials_skips_when_blocked(app, client_app, user, mocker):
    """Credentials fetch is skipped when user is in backoff."""
    user.nc_login = None
    user.nc_locator = None
    user.nc_token = None
    user.nc_last_auto_enroll = None
    db.session.add(user)
    db.session.commit()

    mark_credentials_fetch_failed(user)
    get_creds_mock = mocker.patch("b3desk.nextcloud.get_user_nc_credentials")

    result = update_user_nc_credentials(user)

    assert result is False
    get_creds_mock.assert_not_called()


def test_update_credentials_clears_backoff_on_success(app, client_app, user, mocker):
    """Successful credentials fetch clears backoff."""
    user.nc_login = None
    user.nc_locator = None
    user.nc_token = None
    user.nc_last_auto_enroll = None
    db.session.add(user)
    db.session.commit()

    mark_credentials_fetch_failed(user)
    clear_credentials_fetch_backoff(user)

    mocker.patch(
        "b3desk.nextcloud.get_user_nc_credentials",
        return_value={
            "nclogin": "alice",
            "nclocator": "http://nextcloud.test",
            "nctoken": "token123",
        },
    )

    result = update_user_nc_credentials(user)

    assert result is True
    assert is_credentials_fetch_blocked(user) is False
