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
"""Generate fake users and meetings to populate a development database.

This module is only meant to be used from the development-only ``populate``
CLI command. It depends on ``faker``, imported lazily by the command so that
production deployments never load it.
"""

import random

from faker import Faker
from flask import current_app
from slugify import slugify

from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import DEFAULT_MAX_PARTICIPANTS
from b3desk.models.meetings import AccessLevel
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingAccess
from b3desk.models.meetings import assign_unique_codes
from b3desk.models.users import User
from b3desk.utils import get_random_alphanumeric_string

DEFAULT_LOCALE = "fr_FR"
ADMIN_RATIO = 0.1
DELEGATION_RATIO = 0.3
MAX_DELEGATES_PER_MEETING = 3
FAVORITE_RATIO = 0.2
PASSWORD_LENGTH = 16
EMAIL_TOKEN_LENGTH = 6
GROUP_COUNT = 5
MAX_MEMBERS_PER_GROUP = 100


def make_faker(locale=DEFAULT_LOCALE, seed=None):
    """Build a Faker instance, seeding every random source when seed is given."""
    faker = Faker(locale)
    if seed is not None:
        Faker.seed(seed)
        faker.seed_instance(seed)
        random.seed(seed)
    return faker


def generate_users(faker, count, admin_ratio=ADMIN_RATIO):
    """Create and commit ``count`` random users, a fraction of them being admins."""
    users = []
    for _ in range(count):
        given_name = faker.first_name()
        family_name = faker.last_name()
        token = get_random_alphanumeric_string(EMAIL_TOKEN_LENGTH).lower()
        email = (
            f"{slugify(given_name)}.{slugify(family_name)}.{token}"
            f"@{faker.free_email_domain()}"
        )
        created_at = faker.date_time_between(start_date="-2y")
        users.append(
            User(
                email=email,
                given_name=given_name,
                family_name=family_name,
                preferred_username=faker.user_name(),
                created_at=created_at,
                last_connection_utc_datetime=faker.date_time_between(
                    start_date=created_at
                ),
                admin=random.random() < admin_ratio,
            )
        )
    db.session.add_all(users)
    db.session.commit()
    return users


def generate_meetings(faker, users, count):
    """Create and commit ``count`` random meetings owned by random users."""
    meetings = []
    for _ in range(count):
        auto_start_recording = faker.boolean()
        allow_start_stop_recording = faker.boolean()
        created_at = faker.date_time_between(start_date="-2y")
        meeting = Meeting(
            owner=random.choice(users),
            name=faker.catch_phrase()[:150],
            welcome=faker.sentence(),
            maxParticipants=random.choice([50, 100, 200, DEFAULT_MAX_PARTICIPANTS]),
            duration=current_app.config["DEFAULT_MEETING_DURATION"],
            logoutUrl=current_app.config["MEETING_LOGOUT_URL"],
            attendeePW=get_random_alphanumeric_string(PASSWORD_LENGTH),
            moderatorPW=get_random_alphanumeric_string(PASSWORD_LENGTH),
            created_at=created_at,
            last_connection_utc_datetime=faker.date_time_between(start_date=created_at),
            autoStartRecording=auto_start_recording,
            allowStartStopRecording=allow_start_stop_recording,
            record=auto_start_recording or allow_start_stop_recording,
            webcamsOnlyForModerator=faker.boolean(),
            muteOnStart=faker.boolean(),
            guestPolicy=faker.boolean(),
        )
        db.session.add(meeting)
        assign_unique_codes(meeting)
        meetings.append(meeting)
    db.session.commit()
    return meetings


def generate_delegations(
    users, meetings, ratio=DELEGATION_RATIO, max_delegates=MAX_DELEGATES_PER_MEETING
):
    """Delegate a fraction of meetings to random users other than their owner."""
    count = 0
    for meeting in meetings:
        if random.random() >= ratio:
            continue
        candidates = [user for user in users if user.id != meeting.owner_id]
        delegates = random.sample(
            candidates, min(len(candidates), random.randint(1, max_delegates))
        )
        for delegate in delegates:
            db.session.add(
                MeetingAccess(
                    user_id=delegate.id,
                    meeting_id=meeting.id,
                    level=AccessLevel.DELEGATE,
                )
            )
            count += 1
    db.session.commit()
    return count


def generate_favorites(users, meetings, ratio=FAVORITE_RATIO):
    """Mark a random subset of meetings as favorite for each user."""
    count = 0
    sample_size = round(len(meetings) * ratio)
    for user in users:
        for meeting in random.sample(meetings, min(sample_size, len(meetings))):
            user.favorites.append(meeting)
            count += 1
    db.session.commit()
    return count


def generate_groups(faker, users, count=GROUP_COUNT, max_members=MAX_MEMBERS_PER_GROUP):
    """Create and commit ``count`` random groups with random members."""
    groups = []
    for _ in range(count):
        group = Group(
            name=faker.unique.bs()[:150],
            enable_sip=random.choice([True, False, None]),
            enable_file_sharing=random.choice([True, False, None]),
            enable_ai_summary=random.choice([True, False, None]),
        )
        group.members = random.sample(
            users, min(len(users), random.randint(1, max_members))
        )
        groups.append(group)
    db.session.add_all(groups)
    db.session.commit()
    return groups


def populate(n_users, n_meetings, locale=DEFAULT_LOCALE, seed=None):
    """Populate the database with random users, meetings and their relations."""
    faker = make_faker(locale=locale, seed=seed)
    users = generate_users(faker, n_users)
    meetings = generate_meetings(faker, users, n_meetings) if users else []
    delegations = generate_delegations(users, meetings)
    favorites = generate_favorites(users, meetings)
    groups = generate_groups(faker, users) if users else []
    return {
        "users": len(users),
        "admins": sum(user.admin for user in users),
        "meetings": len(meetings),
        "delegations": delegations,
        "favorites": favorites,
        "groups": len(groups),
    }
