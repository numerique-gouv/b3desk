import hashlib
from datetime import datetime
from datetime import timedelta

from flask import current_app
from flask import url_for

from b3desk.models.roles import Role
from b3desk.utils import secret_key


def get_hash(meeting, role: Role, hash_from_string=False):
    """Generate a hash for meeting access verification based on role."""
    s = f"{meeting.meetingID}|{meeting.attendeePW}|{meeting.name}|{role.name if hash_from_string else role}"
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def get_role(meeting, hashed_role, user=None) -> Role | None:
    """Determine the meeting role based on hash and user."""
    if meeting.user and meeting.user == user:
        return Role.moderator
    elif hashed_role in [
        get_hash(meeting, Role.attendee),
        get_hash(meeting, Role.attendee, hash_from_string=True),
    ]:
        role = Role.attendee
    elif hashed_role in [
        get_hash(meeting, Role.moderator),
        get_hash(meeting, Role.moderator, hash_from_string=True),
    ]:
        role = Role.moderator
    elif hashed_role in [
        get_hash(meeting, Role.authenticated),
        get_hash(meeting, Role.authenticated, hash_from_string=True),
    ]:
        role = (
            Role.authenticated
            if current_app.config["OIDC_ATTENDEE_ENABLED"]
            else Role.attendee
        )
    else:
        role = None
    return role


def get_join_url(
    meeting,
    meeting_role: Role,
    fullname,
    fullname_suffix="",
    quick_meeting=False,
    seconds_before_refresh=None,
    waiting_room=True,
):
    """Return the URL of the BBB meeting URL if available, and the URL of the b3desk 'waiting_meeting' if it is not ready."""
    if waiting_room and not meeting.is_running():
        return url_for(
            "join.waiting_meeting",
            meeting_fake_id=meeting.fake_id,
            hash_=get_hash(meeting, meeting_role),
            fullname=fullname,
            fullname_suffix=fullname_suffix,
            seconds_before_refresh=seconds_before_refresh,
            quick_meeting=quick_meeting,
        )

    if meeting.id:
        meeting.last_connection_utc_datetime = datetime.now()
        meeting.save()

    nickname = f"{fullname} - {fullname_suffix}" if fullname_suffix else fullname
    return meeting.bbb.prepare_request_to_join_bbb(meeting_role, nickname).url


def get_signin_url(meeting, meeting_role: Role):
    """Generate the sign-in URL for a specific role."""
    return url_for(
        "join.signin_meeting",
        meeting_fake_id=meeting.fake_id,
        hash_=get_hash(meeting, meeting_role),
        role=meeting_role,
        _external=True,
        _scheme=current_app.config["PREFERRED_URL_SCHEME"],
    )


def get_mail_signin_hash(meeting_id, expiration_epoch):
    """Generate a hash for mail-based sign-in with expiration."""
    s = f"{meeting_id}-{expiration_epoch}"
    return hashlib.sha256(s.encode("utf-8") + secret_key().encode("utf-8")).hexdigest()


def get_mail_signin_url(meeting):
    """Generate a time-limited sign-in URL for mail invitations."""
    expiration = str((datetime.now() + timedelta(weeks=1)).timestamp()).split(".")[
        0
    ]  # remove milliseconds
    hash_param = get_mail_signin_hash(meeting.fake_id, expiration)
    return url_for(
        "join.signin_mail_meeting",
        meeting_fake_id=meeting.fake_id,
        expiration=expiration,
        hash_=hash_param,
        _external=True,
    )
