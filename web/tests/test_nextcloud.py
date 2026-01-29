from datetime import date

from b3desk import cache
from b3desk.models import db
from b3desk.models.meetings import MeetingFiles
from b3desk.nextcloud import credentials_breaker
from b3desk.nextcloud import is_auth_error
from b3desk.nextcloud import is_nextcloud_available
from b3desk.nextcloud import is_nextcloud_unavailable_error
from b3desk.nextcloud import nextcloud_breaker
from b3desk.nextcloud import update_user_nc_credentials
from b3desk.nextcloud import user_auth_breaker
from flask import url_for
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

    result = is_nextcloud_available(user, verify=True)

    assert result is True


def test_check_connection_missing_credentials(client_app, user, mocker):
    """Connection check fails when credentials are missing."""
    user.nc_login = None
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    result = is_nextcloud_available(user, verify=True)

    assert result is False


def test_check_connection_webdav_error(client_app, user, mocker):
    """Connection check fails on WebDAV error."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list", side_effect=WebDavException)

    result = is_nextcloud_available(user, verify=True)

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

    result = is_nextcloud_available(user, verify=True)

    assert result is False
    with app.app_context():
        assert cache.get(f"nc_unavailable:{user.nc_locator}") is not None


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

    result = is_nextcloud_available(user, verify=True, retry_on_auth_error=True)

    assert result is True
    update_mock.assert_called_once_with(user, force_renew=True)


def test_check_connection_no_retry_by_default(client_app, user, mocker):
    """Connection check does not retry by default."""
    user.nc_login = None
    db.session.add(user)
    db.session.commit()

    update_mock = mocker.patch("b3desk.nextcloud.update_user_nc_credentials")

    result = is_nextcloud_available(user, verify=True)

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

    result = is_nextcloud_available(user, verify=True, retry_on_auth_error=True)

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

    assert user_auth_breaker.is_blocked(user.id) is False

    user_auth_breaker.mark_failed(user.id)
    assert user_auth_breaker.is_blocked(user.id) is True

    user_auth_breaker.clear(user.id)
    assert user_auth_breaker.is_blocked(user.id) is False


def test_check_connection_skips_when_user_auth_blocked(client_app, user, mocker):
    """Connection check returns False immediately when user is blocked."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    user_auth_breaker.mark_failed(user.id)

    list_mock = mocker.patch("webdav3.client.Client.list")

    result = is_nextcloud_available(user, verify=True)

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

    result = is_nextcloud_available(user, verify=True, retry_on_auth_error=True)

    assert result is False
    with app.app_context():
        assert cache.get(f"nc_auth_failed:{user.id}") is not None


def test_check_connection_clears_backoff_on_success(app, client_app, user, mocker):
    """Connection check clears user auth backoff on success."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    user_auth_breaker.mark_failed(user.id)
    assert user_auth_breaker.is_blocked(user.id) is True

    mocker.patch("webdav3.client.Client.list")

    user_auth_breaker.clear(user.id)

    result = is_nextcloud_available(user, verify=True)

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
    assert credentials_breaker.is_blocked(user.id) is True


def test_update_credentials_skips_when_blocked(app, client_app, user, mocker):
    """Credentials fetch is skipped when user is in backoff."""
    user.nc_login = None
    user.nc_locator = None
    user.nc_token = None
    user.nc_last_auto_enroll = None
    db.session.add(user)
    db.session.commit()

    credentials_breaker.mark_failed(user.id)
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

    credentials_breaker.mark_failed(user.id)
    credentials_breaker.clear(user.id)

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
    assert credentials_breaker.is_blocked(user.id) is False


def test_is_nextcloud_available_with_credentials(client_app, user):
    """is_nextcloud_available returns True when user has valid NC credentials."""
    user.nc_login = "alice"
    user.nc_locator = "https://nextcloud.example.com"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    assert is_nextcloud_available(user) is True


def test_is_nextcloud_available_no_credentials(client_app, user):
    """is_nextcloud_available returns False when user has no NC credentials."""
    user.nc_login = None
    user.nc_locator = None
    user.nc_token = None
    db.session.add(user)
    db.session.commit()

    assert is_nextcloud_available(user) is False


def test_is_nextcloud_available_no_locator(client_app, user):
    """is_nextcloud_available returns False when user has no nc_locator."""
    user.nc_login = "alice"
    user.nc_locator = None
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    assert is_nextcloud_available(user) is False


def test_is_nextcloud_unavailable_error_server_error(client_app):
    """is_nextcloud_unavailable_error returns True for 5xx errors."""
    error = ResponseErrorCode("http://test", 500, "Internal Server Error")
    assert is_nextcloud_unavailable_error(error) is True

    error = ResponseErrorCode("http://test", 503, "Service Unavailable")
    assert is_nextcloud_unavailable_error(error) is True


def test_is_nextcloud_unavailable_error_client_error(client_app):
    """is_nextcloud_unavailable_error returns False for 4xx errors."""
    error = ResponseErrorCode("http://test", 404, "Not Found")
    assert is_nextcloud_unavailable_error(error) is False


def test_missing_token_exception(client_app):
    """MissingToken exception can be raised with custom message."""
    from b3desk.nextcloud import MissingToken

    exc = MissingToken("Custom error message")
    assert str(exc) == "Custom error message"
    assert exc.message == "Custom error message"


def test_webdav_error_handler_html_branch(
    client_app, authenticated_user, mocker, nextcloud_credentials, meeting
):
    """WebDAV error handler returns flash + redirect for HTML requests on unavailability."""
    meeting_file = MeetingFiles(
        nc_path="/visio-agents/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)

    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    class FakeClient:
        def list(self):
            return []

        def download_sync(self, remote_path, local_path):
            raise NoConnection("nextcloud.test")

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    url = url_for(
        "meeting_files.download_meeting_files",
        meeting=meeting,
        file_id=meeting_file.id,
    )
    response = client_app.get(url, headers={"Accept": "text/html"}, status=302)

    assert any(
        cat == "error" and "indisponible" in msg for cat, msg in response.flashes
    )


def test_is_nextcloud_available_when_nextcloud_breaker_blocked(client_app, user):
    """is_nextcloud_available returns False when nextcloud breaker is blocked."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    nextcloud_breaker.mark_failed(user.nc_locator)

    assert is_nextcloud_available(user) is False

    nextcloud_breaker.clear(user.nc_locator)
