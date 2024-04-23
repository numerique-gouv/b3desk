# +----------------------------------------------------------------------------+
# | BBB-VISIO                                                                  |
# +----------------------------------------------------------------------------+
#
#   This program is free software: you can redistribute it and/or modify it
# under the terms of the European Union Public License 1.2 version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
import hashlib
from datetime import date
from datetime import datetime
from urllib.parse import urlparse
from urllib.parse import urlunparse

import requests
from flask import current_app

from b3desk.utils import secret_key

from . import db


def make_nextcloud_credentials_request(url, payload, headers):
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if current_app.config.get("FORCE_HTTPS_ON_EXTERNAL_URLS"):
            valid_nclocator = (
                f'//{data["nclocator"]}'
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

    except requests.exceptions.RequestException:
        return None


class TooManyUsers(Exception):
    """Exception raised if email returns more than one user.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="More than one user is using this email"):
        self.message = message
        super().__init__(self.message)


class NoUserFound(Exception):
    """Exception raised if email returns no user.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="No user with this email was found"):
        self.message = message
        super().__init__(self.message)


def get_secondary_identity_provider_token():
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
    return requests.get(
        f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_URI']}/auth/admin/realms/{current_app.config['SECONDARY_IDENTITY_PROVIDER_REALM']}/users",
        headers={
            "Authorization": f"Bearer {access_token}",
            "cache-control": "no-cache",
        },
        params={"email": email},
    )


def get_secondary_identity_provider_id_from_email(email):
    try:
        token_response = get_secondary_identity_provider_token()
        token_response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        current_app.logger.warning(
            "Get token request error: %s, %s", exception, token_response.text
        )
        raise exception
    access_token = token_response.json()["access_token"]

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


def get_user_nc_credentials(preferred_username="", email=""):
    if (
        not current_app.config["NC_LOGIN_API_KEY"]
        or not current_app.config["NC_LOGIN_API_URL"]
        or not current_app.config["FILE_SHARING"]
        or not (preferred_username or email)
    ):
        current_app.logger.info(
            "File sharing deactivated or unable to perform, no connection to Nextcloud instance"
        )
        return {"nctoken": None, "nclocator": None, "nclogin": None}

    nc_username = preferred_username
    if current_app.config["SECONDARY_IDENTITY_PROVIDER_ENABLED"] and email:
        try:
            nc_username = get_secondary_identity_provider_id_from_email(email=email)
        except requests.exceptions.HTTPError:
            pass
        except TooManyUsers as e:
            current_app.logger.warning(e.message)
        except NoUserFound as e:
            current_app.logger.warning(e.message)
    payload = {"username": nc_username}
    headers = {"X-API-KEY": current_app.config["NC_LOGIN_API_KEY"]}
    current_app.logger.info(
        "Retrieve NC credentials from NC_LOGIN_API_URL %s "
        % current_app.config["NC_LOGIN_API_URL"]
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
    return result


def update_user_nc_credentials(user, user_info):
    # preferred_username is login from keycloak, REQUIRED for nc_login connexion
    # data is conveyed like following :
    # user logs in to keycloak
    # visio-agent retrives preferred_username from keycloack ( aka keycloak LOGIN, which is immutable )
    # visio-agent calls EDNAT API for NC_DATA retrieval, passing LOGIN as postData
    # visio-agent can now connect to remote NC with NC_DATA
    if (
        user.nc_last_auto_enroll
        and user.nc_locator
        and user.nc_token
        and (
            (remaining_time := (datetime.now() - user.nc_last_auto_enroll)).days
            <= current_app.config["NC_LOGIN_TIMEDELTA_DAYS"]
        )
    ):
        current_app.logger.info(
            "Nextcloud login for user %s not to be refreshed for %s",
            user,
            remaining_time,
        )
        return False

    preferred_username = (
        user_info.get("preferred_username")
        if current_app.config["FILE_SHARING"]
        else None
    )

    if current_app.config["SECONDARY_IDENTITY_PROVIDER_ENABLED"]:
        data = get_user_nc_credentials(
            email=(
                user_info.get("email") if current_app.config["FILE_SHARING"] else None
            )
        )
    else:
        data = get_user_nc_credentials(preferred_username=preferred_username)

    if data["nclogin"] is None or data["nclocator"] is None or data["nctoken"] is None:
        current_app.logger.info(
            "No new Nextcloud enroll needed for user %s with those data %s", user, data
        )
        nc_last_auto_enroll = None
    else:
        current_app.logger.info("New Nextcloud enroll for user %s", data["nclogin"])
        nc_last_auto_enroll = datetime.now()

    user.nc_locator = data["nclocator"]
    user.nc_token = data["nctoken"]
    user.nc_login = data["nclogin"]
    user.nc_last_auto_enroll = nc_last_auto_enroll
    return True


def get_or_create_user(user_info):
    given_name = user_info["given_name"]
    family_name = user_info["family_name"]
    email = user_info["email"].lower()

    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            email=email,
            given_name=given_name,
            family_name=family_name,
            last_connection_utc_datetime=datetime.utcnow(),
        )
        update_user_nc_credentials(user, user_info)
        user.save()

    else:
        user_has_changed = update_user_nc_credentials(user, user_info)

        if user.given_name != given_name:
            user.given_name = given_name
            user_has_changed = True

        if user.family_name != family_name:
            user.family_name = family_name
            user_has_changed = True

        if (
            not user.last_connection_utc_datetime
            or user.last_connection_utc_datetime.date() < date.today()
        ):
            user.last_connection_utc_datetime = datetime.utcnow()
            user_has_changed = True

        if user_has_changed:
            user.save()

    return user


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(150), unique=True)
    given_name = db.Column(db.Unicode(50))
    family_name = db.Column(db.Unicode(50))
    nc_locator = db.Column(db.Unicode(255))
    nc_login = db.Column(db.Unicode(255))
    nc_token = db.Column(db.Unicode(255))
    nc_last_auto_enroll = db.Column(db.DateTime)
    last_connection_utc_datetime = db.Column(db.DateTime)

    meetings = db.relationship("Meeting", back_populates="user")

    @property
    def fullname(self):
        return f"{self.given_name} {self.family_name}"

    @property
    def hash(self):
        s = f"{self.email}|{secret_key()}"
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    @property
    def can_create_meetings(self):
        return len(self.meetings) < current_app.config["MAX_MEETINGS_PER_USER"]

    @property
    def mail_domain(self):
        return self.email.split("@")[1] if self.email and "@" in self.email else None

    def save(self):
        db.session.add(self)
        db.session.commit()

    def disable_nextcloud(self):
        self.nc_login = None
        self.nc_locator = None
        self.nc_token = None
        self.nc_last_auto_enroll = None
        self.save()
