# +----------------------------------------------------------------------------+
# | B3DESK                                                                  |
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
from datetime import timezone

from flask import current_app

from b3desk.nextcloud import update_user_nc_credentials
from b3desk.utils import secret_key

from . import db


def get_or_create_user(user_info):
    """Get existing user by email or create a new user from user_info dictionary.

    Updates user information if any fields have changed and saves to database.
    """
    given_name = user_info["given_name"]
    family_name = user_info["family_name"]
    preferred_username = user_info.get("preferred_username")
    email = user_info["email"].lower()

    user = db.session.query(User).filter(User.email == email).first()

    if user is None:
        user = User(
            email=email,
            given_name=given_name,
            family_name=family_name,
            preferred_username=preferred_username,
            last_connection_utc_datetime=datetime.now(timezone.utc),
        )
        update_user_nc_credentials(user)
        db.session.add(user)
        db.session.commit()

    else:
        user_has_changed = update_user_nc_credentials(user)

        if user.given_name != given_name:
            user.given_name = given_name
            user_has_changed = True

        if user.family_name != family_name:
            user.family_name = family_name
            user_has_changed = True

        if user.preferred_username != preferred_username:
            user.preferred_username = preferred_username
            user_has_changed = True

        if (
            not user.last_connection_utc_datetime
            or user.last_connection_utc_datetime.date() < date.today()
        ):
            user.last_connection_utc_datetime = datetime.now(timezone.utc)
            user_has_changed = True

        if user_has_changed:
            db.session.add(user)
            db.session.commit()

    return user


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(150), unique=True)
    given_name = db.Column(db.Unicode(50))
    family_name = db.Column(db.Unicode(50))
    preferred_username = db.Column(db.Unicode(50), nullable=True)
    nc_locator = db.Column(db.Unicode(255))
    nc_login = db.Column(db.Unicode(255))
    nc_token = db.Column(db.Unicode(255))
    nc_last_auto_enroll = db.Column(db.DateTime)
    last_connection_utc_datetime = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    meetings = db.relationship("Meeting", back_populates="user")

    @property
    def fullname(self):
        """Return user's full name combining given name and family name."""
        return f"{self.given_name} {self.family_name}"

    @property
    def hash(self):
        """Generate SHA1 hash from user's email and application secret key."""
        s = f"{self.email}|{secret_key()}"
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    @property
    def can_create_meetings(self):
        """Check if user has not reached the maximum number of meetings allowed."""
        return len(self.meetings) < current_app.config["MAX_MEETINGS_PER_USER"]

    @property
    def has_nc_credentials(self):
        """Check if user has valid Nextcloud credentials (login, token, and locator)."""
        return self.nc_login and self.nc_token and self.nc_locator

    @property
    def mail_domain(self):
        """Extract and return the domain part of the user's email address."""
        return self.email.split("@")[1] if self.email and "@" in self.email else None

    def disable_nextcloud(self):
        """Clear all Nextcloud credentials and save to database."""
        self.nc_login = None
        self.nc_locator = None
        self.nc_token = None
        self.nc_last_auto_enroll = None
        db.session.add(self)
        db.session.commit()
