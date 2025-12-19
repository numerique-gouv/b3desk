from datetime import datetime
from datetime import timedelta
from urllib.parse import urlparse
from urllib.parse import urlunparse

import requests
from flask import current_app
from flask import g
from webdav3.client import Client as webdavClient
from webdav3.exceptions import WebDavException


def get_nextcloud_available():
    """Lazy evaluation of Nextcloud availability, cached in flask.g."""
    if not hasattr(g, "nextcloud_available"):
        if g.user and g.user.has_nc_credentials:
            g.nextcloud_available = nextcloud_healthcheck(g.user)
        else:
            g.nextcloud_available = False
    return g.nextcloud_available


def create_webdav_client(user) -> webdavClient | None:
    """Create a WebDAV client configured for a user's Nextcloud account."""
    if not user.nc_login or not user.nc_locator or not user.nc_token:
        return None

    options = {
        "webdav_root": f"/remote.php/dav/files/{user.nc_login}/",
        "webdav_hostname": user.nc_locator,
        "webdav_verbose": True,
        "webdav_token": user.nc_token,
    }
    return webdavClient(options)


def make_nextcloud_credentials_request(url, payload, headers):
    """Make a POST request to Nextcloud API to retrieve credentials.

    Handles URL validation and HTTPS enforcement based on configuration.
    """
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(
            "Unable to contact %s with payload %s and header %s, %s",
            url,
            payload,
            headers,
            e,
        )
        return None

    if current_app.config.get("FORCE_HTTPS_ON_EXTERNAL_URLS"):
        valid_nclocator = (
            f"//{data['nclocator']}"
            if not (
                data["nclocator"].startswith("//")
                or data["nclocator"].startswith("http://")
                or data["nclocator"].startswith("https://")
            )
            else data["nclocator"]
        )
        parsed_url = urlparse(valid_nclocator)
        if parsed_url.scheme != "https":
            data["nclocator"] = urlunparse(parsed_url._replace(scheme="https"))

    return data


class MissingToken(Exception):
    """Exception raised if unable to get token."""

    def __init__(self, message="No token given for the B3Desk instance"):
        self.message = message
        super().__init__(self.message)


class TooManyUsers(Exception):
    """Exception raised if email returns more than one user."""

    def __init__(self, message="More than one user is using this email"):
        self.message = message
        super().__init__(self.message)


class NoUserFound(Exception):
    """Exception raised if email returns no user."""

    def __init__(self, message="No user with this email was found"):
        self.message = message
        super().__init__(self.message)


def get_secondary_identity_provider_token():
    """Retrieve OAuth access token from secondary identity provider using client credentials."""
    # TODO: replace this with authlib
    return requests.post(
        f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_URI']}/auth/realms/{current_app.config['SECONDARY_IDENTITY_PROVIDER_REALM']}/protocol/openid-connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_CLIENT_ID']}",
            "client_secret": f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_CLIENT_SECRET']}",
        },
    )


def get_secondary_identity_provider_users_from_email(email, access_token):
    """Query secondary identity provider API to retrieve users matching the given email."""
    return requests.get(
        f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_URI']}/auth/admin/realms/{current_app.config['SECONDARY_IDENTITY_PROVIDER_REALM']}/users",
        headers={
            "Authorization": f"Bearer {access_token}",
            "cache-control": "no-cache",
        },
        params={"email": email},
    )


def get_secondary_identity_provider_id_from_email(email):
    """Get username from secondary identity provider by email.

    Returns the unique username associated with the given email address.
    Raises exceptions if no user or multiple users are found.
    """
    try:
        token_response = get_secondary_identity_provider_token()
        token_response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        current_app.logger.warning(
            "Get token request error: %s, %s", exception, token_response.text
        )
        raise exception

    try:
        access_token = token_response.json()["access_token"]
        if not access_token:
            raise MissingToken(
                f"No token given for the B3Desk instance, {token_response}"
            )
    except (AttributeError, KeyError) as err:
        raise MissingToken(
            f"No token given for the B3Desk instance, {token_response}"
        ) from err

    try:
        users_response = get_secondary_identity_provider_users_from_email(
            email=email, access_token=access_token
        )
        users_response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        current_app.logger.warning(
            "Get user from email request error: %s, %s", exception, users_response.text
        )
        raise exception
    found_users = users_response.json()
    if (user_count := len(found_users)) > 1:
        raise TooManyUsers(f"There are {user_count} users with the email {email}")
    elif user_count < 1:
        raise NoUserFound(f"There are no users with the email {email}")

    [user] = found_users
    return user["username"]


def has_secondary_identity_with_email(email):
    """Check if secondary identity provider is enabled and email is present."""
    return current_app.config["SECONDARY_IDENTITY_PROVIDER_ENABLED"] and email


def can_get_file_sharing_credentials(preferred_username, email):
    """Determine if file sharing credentials can be retrieved for the user."""
    is_cloud_configured = (
        current_app.config["NC_LOGIN_API_KEY"]
        and current_app.config["NC_LOGIN_API_URL"]
        and current_app.config["FILE_SHARING"]
    )
    return (
        is_cloud_configured
        and has_secondary_identity_with_email(email)
        or preferred_username
    )


def get_user_nc_credentials(user):
    """Retrieve Nextcloud credentials (login, token, locator) for the given user.

    Uses secondary identity provider if configured, otherwise uses preferred_username.
    """
    if not can_get_file_sharing_credentials(user.preferred_username, user.email):
        current_app.logger.info(
            "File sharing deactivated or unable to perform, no connection to Nextcloud instance"
        )
        return {"nctoken": None, "nclocator": None, "nclogin": None}

    nc_username = user.preferred_username
    if has_secondary_identity_with_email(user.email):
        try:
            nc_username = get_secondary_identity_provider_id_from_email(
                email=user.email
            )
        except requests.exceptions.HTTPError:
            pass
        except (TooManyUsers, NoUserFound) as e:
            current_app.logger.warning(e)

    payload = {"username": nc_username}
    headers = {"X-API-KEY": current_app.config["NC_LOGIN_API_KEY"]}
    current_app.logger.info(
        "Retrieve NC credentials from NC_LOGIN_API_URL %s for user %s",
        current_app.config["NC_LOGIN_API_URL"],
        nc_username,
    )
    result = make_nextcloud_credentials_request(
        current_app.config["NC_LOGIN_API_URL"], payload, headers
    )
    if not result:
        current_app.logger.error(
            "Cannot contact NC %s, returning None values",
            current_app.config["NC_LOGIN_API_URL"],
        )
        return {"nctoken": None, "nclocator": None, "nclogin": None}

    if "nclogin" not in result:
        result["nclogin"] = nc_username

    return result


def update_user_nc_credentials(user, force_renew=False):
    """Update user's Nextcloud credentials if needed.

    Credentials are renewed if force_renew is True or if the last update exceeds the configured timedelta.
    Returns True if credentials were updated, False otherwise.
    """
    # preferred_username is login from keycloak, REQUIRED for nc_login connexion
    # data is conveyed like following :
    # user logs in to keycloak
    # visio-agent retrives preferred_username from keycloack ( aka keycloak LOGIN, which is immutable )
    # visio-agent calls EDNAT API for NC_DATA retrieval, passing LOGIN as postData
    # visio-agent can now connect to remote NC with NC_DATA
    if not current_app.config["FILE_SHARING"]:
        return False

    if (
        not force_renew
        and user.nc_last_auto_enroll
        and user.nc_locator
        and user.nc_token
        and (
            (elapsed_time := (datetime.now() - user.nc_last_auto_enroll)).days
            <= current_app.config["NC_LOGIN_TIMEDELTA_DAYS"]
        )
    ):
        current_app.logger.info(
            "Nextcloud login for user %s not to be refreshed for %s",
            user,
            timedelta(days=current_app.config["NC_LOGIN_TIMEDELTA_DAYS"])
            - elapsed_time,
        )
        return False

    data = get_user_nc_credentials(user)
    if (
        not data
        or data.get("error")
        or data["nclogin"] is None
        or data["nclocator"] is None
        or data["nctoken"] is None
    ):
        current_app.logger.info(
            "No new Nextcloud enroll needed for user %s with those data %s", user, data
        )
        nc_last_auto_enroll = None
    else:
        current_app.logger.info("New Nextcloud enroll for user %s", data["nclogin"])
        nc_last_auto_enroll = datetime.now()

    user.nc_locator = data.get("nclocator")
    user.nc_token = data.get("nctoken")
    user.nc_login = data.get("nclogin")
    user.nc_last_auto_enroll = nc_last_auto_enroll
    return True


def nextcloud_healthcheck(user):
    """Perform a simple WebDAV operation to check the server connection.

    On errors, attempt to renew the credentials and perform one single retry.
    """

    def _healthcheck():
        try:
            if (client := create_webdav_client(user)) is None:
                return False

            client.list()
        except WebDavException as exception:
            current_app.logger.warning("WebDAV error: %s", exception)
            return False
        return True

    if _healthcheck():
        return True

    update_user_nc_credentials(user, force_renew=True)

    if _healthcheck():
        return True

    return False
