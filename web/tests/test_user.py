from datetime import date

import pytest
from freezegun import freeze_time

from b3desk.models import db
from b3desk.models.users import User
from b3desk.models.users import get_or_create_user
from b3desk.models.users import make_nextcloud_credentials_request


def test_get_or_create_user(client_app):
    user_info = {
        "given_name": "Alice",
        "family_name": "Cooper",
        "preferred_username": "alice",
        "email": "alice@mydomain.test",
    }
    get_or_create_user(user_info)

    user = db.session.get(User, 1)
    assert user.given_name == "Alice"
    assert user.family_name == "Cooper"
    assert user.email == "alice@mydomain.test"
    assert user.last_connection_utc_datetime.date() == date.today()


def test_update_last_connection_if_more_than_24h(client_app):
    user_info = {
        "given_name": "Alice",
        "family_name": "Cooper",
        "preferred_username": "alice",
        "email": "alice@mydomain.test",
    }
    with freeze_time("2021-08-10"):
        get_or_create_user(user_info)

    with freeze_time("2021-08-11"):
        user = db.session.get(User, 1)
        assert user.last_connection_utc_datetime.date() == date(2021, 8, 10)

        get_or_create_user(user_info)

        assert user.last_connection_utc_datetime.date() == date(2021, 8, 11)


def test_make_nextcloud_credentials_request_with_scheme_response(
    client_app, app, cloud_service_response, mocker
):
    assert cloud_service_response.data["nclocator"].startswith("http://")
    mocker.patch(
        "b3desk.models.users.requests.post", return_value=cloud_service_response
    )
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = False
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("http://")


@pytest.mark.secure
def test_make_nextcloud_credentials_request_with_secure_response(
    client_app, app, cloud_service_response, mocker
):
    assert cloud_service_response.data["nclocator"].startswith("https://")
    mocker.patch(
        "b3desk.models.users.requests.post", return_value=cloud_service_response
    )
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = False
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("https://")


def test_make_nextcloud_credentials_request_force_secure_for_unsecure(
    client_app, app, cloud_service_response, mocker
):
    assert cloud_service_response.data["nclocator"].startswith("http://")
    mocker.patch(
        "b3desk.models.users.requests.post", return_value=cloud_service_response
    )
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = True
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("https://")


@pytest.mark.no_scheme
def test_make_nextcloud_credentials_request_force_secure_for_missing_scheme(
    client_app, app, cloud_service_response, mocker
):
    assert not cloud_service_response.data["nclocator"].startswith("http")
    mocker.patch(
        "b3desk.models.users.requests.post", return_value=cloud_service_response
    )
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = True
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("https://")
