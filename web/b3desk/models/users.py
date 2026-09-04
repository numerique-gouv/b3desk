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
from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

from flask import current_app
from sqlalchemy import Unicode
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from b3desk.nextcloud import update_user_nc_credentials
from b3desk.utils import secret_key
from b3desk.utils.mailing import EMAIL_DELAYS

from . import db
from .information import compute_first_mail_deadline
from .information import get_entities_due_for_next_mail
from .information import ready_for_final_deletion

if TYPE_CHECKING:
    from .groups import Group
    from .meetings import Meeting
    from .meetings import MeetingAccess


def get_or_create_user(user_info):
    """Get existing user by email or create a new user from user_info dictionary.

    Updates user information if any fields have changed and saves to database.
    """
    mapping = current_app.config["OIDC_CLAIMS_MAPPING"]
    given_name = user_info.get(mapping.get("given_name", "given_name"), "")
    family_name = user_info.get(mapping.get("family_name", "family_name"), "")
    preferred_username = user_info.get(
        mapping.get("preferred_username", "preferred_username")
    )
    email = user_info[mapping.get("email", "email")].lower()

    user = User.get_user_by_email(email)

    if user is None:
        user = User(
            email=email,
            given_name=given_name,
            family_name=family_name,
            preferred_username=preferred_username,
            last_connection_utc_datetime=datetime.now(UTC),
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
            user.last_connection_utc_datetime = datetime.now(UTC)
            user_has_changed = True

        if user_has_changed:
            db.session.add(user)
            db.session.commit()

    return user


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(Unicode(255), unique=True)
    given_name: Mapped[str | None] = mapped_column(Unicode(50))
    family_name: Mapped[str | None] = mapped_column(Unicode(50))
    preferred_username: Mapped[str | None] = mapped_column(Unicode(255))
    nc_locator: Mapped[str | None] = mapped_column(Unicode(255))
    nc_login: Mapped[str | None] = mapped_column(Unicode(255))
    nc_token: Mapped[str | None] = mapped_column(Unicode(255))
    nc_last_auto_enroll: Mapped[datetime | None]
    last_connection_utc_datetime: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    admin: Mapped[bool] = mapped_column(default=False)
    information_level: Mapped[int] = mapped_column(default=0)
    information_sent_at: Mapped[datetime | None]

    meetings: Mapped[list[Meeting]] = relationship(back_populates="owner")
    favorites: Mapped[list[Meeting]] = relationship(
        secondary="favorite", back_populates="favorite_of"
    )
    groups: Mapped[list[Group]] = relationship(
        secondary="group_member", back_populates="members"
    )
    user_meeting_access: Mapped[list[MeetingAccess]] = relationship(
        back_populates="user"
    )

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
        return bool(self.nc_login and self.nc_token and self.nc_locator)

    @property
    def mail_domain(self):
        """Extract and return the domain part of the user's email address."""
        return self.email.split("@")[1] if self.email and "@" in self.email else None

    @property
    def get_all_delegated_meetings(self):
        from b3desk.models.meetings import AccessLevel
        from b3desk.models.meetings import Meeting
        from b3desk.models.meetings import MeetingAccess

        return db.session.scalars(
            db.select(Meeting)
            .join(MeetingAccess)
            .where(
                MeetingAccess.user_id == self.id,
                MeetingAccess.level == AccessLevel.DELEGATE,
            )
        ).all()

    @classmethod
    def get_user_by_email(cls, email):
        return db.session.scalars(db.select(cls).where(cls.email == email)).first()

    @property
    def can_use_file_sharing(self):
        if not self.groups:
            return current_app.config["FILE_SHARING"]
        if any(group.enable_file_sharing for group in self.groups):
            return True
        if all(group.enable_file_sharing is False for group in self.groups):
            return False
        return current_app.config["FILE_SHARING"]

    @property
    def can_use_sip(self):
        if not self.groups:
            return current_app.config["ENABLE_SIP"]
        if any(group.enable_sip for group in self.groups):
            return True
        if all(group.enable_sip is False for group in self.groups):
            return False
        return current_app.config["ENABLE_SIP"]

    @property
    def can_use_ai_summary(self):
        if not self.groups:
            return current_app.config["ENABLE_AI_SUMMARY"]
        if any(group.enable_ai_summary for group in self.groups):
            return True
        if all(group.enable_ai_summary is False for group in self.groups):
            return False
        return current_app.config["ENABLE_AI_SUMMARY"]


def get_inactive_users_to_delete():
    """Return users that are ready to be deleted."""
    return db.session.scalars(
        db.select(User).where(ready_for_final_deletion(User, datetime.now(UTC)))
    ).all()


def clean_db_and_delete_user(user, force=False):
    from b3desk.models.meetings import MeetingFiles
    from b3desk.models.meetings import clean_db_and_delete_meeting

    for meeting_file in db.session.scalars(
        db.select(MeetingFiles).where(MeetingFiles.owner_id == user.id)
    ):
        db.session.delete(meeting_file)

    for meeting in user.meetings:
        clean_db_and_delete_meeting(meeting, force)

    for access in user.user_meeting_access:
        db.session.delete(access)

    db.session.delete(user)
    db.session.commit()


def as_naive(value):
    """Strip an aware datetime's timezone so it can be compared to values read from the database."""
    return value.replace(tzinfo=None) if value.tzinfo else value


def get_user_effective_activity(user):
    """Return a user's most recent activity, from their own account or their meetings."""
    activities = [user.last_connection_utc_datetime or user.created_at]
    activities += [
        meeting.last_connection_utc_datetime or meeting.created_at
        for meeting in user.meetings
    ]
    return max(as_naive(activity) for activity in activities)


def update_reactivated_users(first_mail_deadline):
    """Reset information_level for users reactivated since last email."""
    reactivated_users = db.session.scalars(
        db.select(User).where(User.information_level > 0)
    ).all()
    for user in reactivated_users:
        if get_user_effective_activity(user) > first_mail_deadline:
            user.information_level = 0
            user.information_sent_at = None
    db.session.commit()


def get_inactive_users_to_inform():
    """Advance each user's information_level by one step."""
    now = datetime.now(UTC)
    account_inactivity_period = timedelta(
        days=current_app.config["INACTIVITY_TIMER_CLEANUP_ACCOUNT"]
    )
    first_mail_deadline = as_naive(
        compute_first_mail_deadline(now, account_inactivity_period)
    )

    update_reactivated_users(first_mail_deadline)

    never_informed_users = db.session.scalars(
        db.select(User).where(User.information_level == 0)
    ).all()
    users = [
        (user, EMAIL_DELAYS[0], 1)
        for user in never_informed_users
        if get_user_effective_activity(user) <= first_mail_deadline
    ]
    users += get_entities_due_for_next_mail(User, now)

    return users
