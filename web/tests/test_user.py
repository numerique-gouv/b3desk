from datetime import date

import pytest
import requests
from time_machine import travel

from b3desk.models import db
from b3desk.models.users import NoUserFound
from b3desk.models.users import TooManyUsers
from b3desk.models.users import User
from b3desk.models.users import get_or_create_user
from b3desk.models.users import get_secondary_identity_provider_id_from_email
from b3desk.models.users import make_nextcloud_credentials_request


def test_get_or_create_user(client_app):
    assert db.session.get(User, 1) is None

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
    with travel("2021-08-10 12:00:00"):
        get_or_create_user(user_info)

    with travel("2021-08-11 12:00:00"):
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


def test_get_secondary_identity_provider_id_from_email_token_error(
    client_app, mocker, caplog
):
    class TokenErrorAnswer:
        text = "Unable to get token"

        def raise_for_status():
            raise requests.exceptions.HTTPError

    mocker.patch(
        "b3desk.models.users.get_secondary_identity_provider_token",
        return_value=TokenErrorAnswer,
    )
    with pytest.raises(requests.exceptions.HTTPError):
        get_secondary_identity_provider_id_from_email("jean.espece@rock.org")
    assert "Get token request error:" in caplog.text


def test_get_secondary_identity_provider_id_from_email_request_error(
    client_app, mocker, caplog, valid_secondary_identity_token
):
    class RequestErrorAnswer:
        text = "Unable to ask identity provider"

        def raise_for_status():
            raise requests.exceptions.HTTPError

    mocker.patch(
        "b3desk.models.users.get_secondary_identity_provider_users_from_email",
        return_value=RequestErrorAnswer,
    )
    with pytest.raises(requests.exceptions.HTTPError):
        get_secondary_identity_provider_id_from_email("michel.vendeur@rock.org")
    assert "Get user from email request error:" in caplog.text


def test_get_secondary_identity_provider_id_from_email_many_users(
    client_app, app, mocker, valid_secondary_identity_token
):
    class ManyUsersAnswer:
        def raise_for_status():
            pass

        def json():
            return [{"username": "freddy"}, {"username": "fred"}]

    mocker.patch(
        "b3desk.models.users.get_secondary_identity_provider_users_from_email",
        return_value=ManyUsersAnswer,
    )
    with pytest.raises(TooManyUsers):
        get_secondary_identity_provider_id_from_email("frederick.mercure@rock.org")


def test_get_secondary_identity_provider_id_from_email_no_user(
    client_app, app, mocker, valid_secondary_identity_token
):
    class NoUsersAnswer:
        def raise_for_status():
            pass

        def json():
            return []

    mocker.patch(
        "b3desk.models.users.get_secondary_identity_provider_users_from_email",
        return_value=NoUsersAnswer,
    )
    with pytest.raises(NoUserFound):
        get_secondary_identity_provider_id_from_email("blaireau.riviere@rock.org")
