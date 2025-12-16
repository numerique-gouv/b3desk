from b3desk.models import db
from b3desk.nextcloud import nextcloud_healthcheck
from webdav3.exceptions import WebDavException


def test_healthcheck_success_first_try(client_app, user, mocker):
    """Healthcheck passes on first attempt."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list")

    result = nextcloud_healthcheck(user)

    assert result is True
    assert user.nc_login == "alice"


def test_healthcheck_success_after_retry(client_app, user, mocker):
    """Healthcheck fails first, succeeds after credential renewal."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    call_count = 0

    def webdav_list():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise WebDavException()

    mocker.patch("webdav3.client.Client.list", side_effect=webdav_list)

    result = nextcloud_healthcheck(user)

    assert result is True
    assert call_count == 2
    assert user.nc_login is not None


def test_healthcheck_fails_preserves_credentials(client_app, user, mocker):
    """Healthcheck fails twice but preserves user credentials."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list", side_effect=WebDavException)

    result = nextcloud_healthcheck(user)

    assert result is False
    assert user.nc_login is not None
    assert user.nc_locator is not None
    assert user.nc_token is not None


def test_healthcheck_missing_login(client_app, user, mocker):
    """Healthcheck fails when nc_login is missing and cannot be renewed."""
    user.nc_login = None
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list")
    mocker.patch(
        "b3desk.nextcloud.make_nextcloud_credentials_request",
        return_value={"nctoken": None, "nclocator": None, "nclogin": None},
    )

    result = nextcloud_healthcheck(user)

    assert result is False


def test_healthcheck_missing_locator(client_app, user, mocker):
    """Healthcheck fails when nc_locator is missing and cannot be renewed."""
    user.nc_login = "alice"
    user.nc_locator = None
    user.nc_token = "token123"
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list")
    mocker.patch(
        "b3desk.nextcloud.make_nextcloud_credentials_request",
        return_value={"nctoken": None, "nclocator": None, "nclogin": None},
    )

    result = nextcloud_healthcheck(user)

    assert result is False


def test_healthcheck_missing_token(client_app, user, mocker):
    """Healthcheck fails when nc_token is missing and cannot be renewed."""
    user.nc_login = "alice"
    user.nc_locator = "http://nextcloud.test"
    user.nc_token = None
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list")
    mocker.patch(
        "b3desk.nextcloud.make_nextcloud_credentials_request",
        return_value={"nctoken": None, "nclocator": None, "nclogin": None},
    )

    result = nextcloud_healthcheck(user)

    assert result is False


def test_healthcheck_missing_credentials_renewed(client_app, user, mocker):
    """Healthcheck succeeds when missing credentials are renewed."""
    user.nc_login = None
    user.nc_locator = None
    user.nc_token = None
    db.session.add(user)
    db.session.commit()

    mocker.patch("webdav3.client.Client.list")

    result = nextcloud_healthcheck(user)

    assert result is True
    assert user.nc_login is not None
