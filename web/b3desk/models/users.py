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
import json
from datetime import UTC
from datetime import date
from datetime import datetime
from typing import TYPE_CHECKING

from flask import current_app
from sqlalchemy import Unicode
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from b3desk.models.groups import Group
from b3desk.nextcloud import update_user_nc_credentials
from b3desk.utils import secret_key

from . import db

if TYPE_CHECKING:
    from .groups import Group
    from .meetings import Meeting
    from .meetings import MeetingAccess


CODACA = {
    "000": "Étranger",
    "001": "Paris",
    "002": "Aix-Marseille",
    "003": "Besançon",
    "004": "Bordeaux",
    "005": "Caen",
    "006": "Clermont-Ferrand",
    "007": "Dijon",
    "008": "Grenoble",
    "009": "Lille",
    "010": "Lyon",
    "011": "Montpellier",
    "012": "Nancy-Metz",
    "013": "Poitiers",
    "014": "Rennes",
    "015": "Strasbourg",
    "016": "Toulouse",
    "017": "Nantes",
    "018": "Orléans-Tours",
    "019": "Reims",
    "020": "Amiens",
    "021": "Rouen",
    "022": "Limoges",
    "023": "Nice",
    "024": "Créteil",
    "025": "Versailles",
    "027": "Corse",
    "028": "La Réunion",
    "031": "Martinique",
    "032": "Guadeloupe",
    "033": "Guyane",
    "040": "Nouvelle Calédonie",
    "041": "Polynésie Française",
    "042": "Wallis et Futuna",
    "043": "Mayotte",
    "044": "St Pierre et Miquelon",
}


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

    meta_data = json.dumps(
        {
            "academic_domain": user_info.get(mapping.get("FrEduAca", "FrEduAca"), ""),
            "academic_code": user_info.get(mapping.get("codaca", "codaca"), ""),
        }
    )

    user = User.get_user_by_email(email)

    if user is None:
        user = User(
            email=email,
            given_name=given_name,
            family_name=family_name,
            preferred_username=preferred_username,
            last_connection_utc_datetime=datetime.now(UTC),
            meta_data=meta_data,
        )
        update_user_nc_credentials(user)
        db.session.add(user)
        db.session.commit()

    else:
        user_changes = update_user_nc_credentials(user) or {}

        if user.given_name != given_name:
            user.given_name = given_name
            user_changes["given_name"] = given_name

        if user.family_name != family_name:
            user.family_name = family_name
            user_changes["family_name"] = family_name

        if user.preferred_username != preferred_username:
            user.preferred_username = preferred_username
            user_changes["preferred_username"] = preferred_username

        if (
            not user.last_connection_utc_datetime
            or user.last_connection_utc_datetime.date() < date.today()
        ):
            user.last_connection_utc_datetime = datetime.now(UTC)
            user_changes["last_connection_utc_datetime"] = datetime.now(UTC)

        if user.meta_data and user.meta_data != meta_data:
            user.meta_data = meta_data
            user_changes["meta_data"] = meta_data

        if user_changes:
            db.session.add(user)
            db.session.commit()
            current_app.logger.info("%s has changed %s", user.email, user_changes)

    user.automatic_group_affiliation()

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
    meta_data: Mapped[str | None] = mapped_column(db.JSON)

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
    excluded_groups = db.relationship(
        "Group", secondary="excludelist", back_populates="excluded_users"
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
        """Extract and return the domain from meta_data or part of the user's email address."""
        if self.meta_data:
            user_meta_data = json.loads(self.meta_data)
            return user_meta_data["academic_domain"]
        return self.email.split("@")[1] if self.email and "@" in self.email else None

    @property
    def academic_code(self):
        """Return the user's académie code (CODACA) from meta_data, if any."""
        if self.meta_data:
            return json.loads(self.meta_data)["academic_code"]
        return None

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

    def automatic_group_affiliation(self):
        groups = db.session.execute(db.select(Group)).scalars().all()
        added_groups = []
        removed_groups = []
        for group in groups:
            if (
                self not in group.excluded_users
                and self.academic_code in group.academic_codes
                and self not in group.members
            ):
                group.members.append(self)
                added_groups.append((group.id, group.name))
            if (
                self in group.excluded_users
                or self.academic_code not in group.academic_codes
            ) and self in group.members:
                group.members.remove(self)
                removed_groups.append((group.id, group.name))

        for group in added_groups:
            current_app.logger.info(
                "%s added in group %s %s", self.fullname, group[0], group[1]
            )
        for group in removed_groups:
            current_app.logger.info(
                "%s removed from group %s %s", self.fullname, group[0], group[1]
            )

        if added_groups or removed_groups:
            db.session.commit()
