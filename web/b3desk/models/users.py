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


def get_user_nc_credentials(username):
    if (
        not current_app.config["NC_LOGIN_API_KEY"]
        or not current_app.config["NC_LOGIN_API_URL"]
        or not current_app.config["FILE_SHARING"]
        or not username
    ):
        current_app.logger.debug(
            "File sharing deactivated or unable to perform, no connection to Nextcloud instance"
        )
        return {"nctoken": None, "nclocator": None, "nclogin": None}

    payload = {"username": username}
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
            (datetime.now() - user.nc_last_auto_enroll).days
            <= current_app.config["NC_LOGIN_TIMEDELTA_DAYS"]
        )
    ):
        return False

    preferred_username = (
        user_info.get("preferred_username")
        if current_app.config["FILE_SHARING"]
        else None
    )
    data = get_user_nc_credentials(preferred_username)
    if (
        preferred_username is None
        or data["nclocator"] is None
        or data["nctoken"] is None
    ):
        nc_last_auto_enroll = None
    else:
        nc_last_auto_enroll = datetime.now()

    user.nc_locator = data["nclocator"]
    user.nc_token = data["nctoken"]
    user.nc_login = preferred_username
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

    def save(self):
        db.session.add(self)
        db.session.commit()

    def disable_nextcloud(self):
        self.nc_login = None
        self.nc_locator = None
        self.nc_token = None
        self.nc_last_auto_enroll = None
        self.save()
