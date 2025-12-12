import hashlib
from datetime import datetime
from datetime import timedelta

from flask import current_app
from flask import render_template
from flask import url_for

from b3desk.models import db
from b3desk.models.roles import Role
from b3desk.utils import secret_key


def get_hash(meeting, role: Role, hash_from_string=False):
    """Generate a hash for meeting access verification based on role."""
    name = meeting.name or current_app.config["QUICK_MEETING_DEFAULT_NAME"]
    s = f"{meeting.meetingID}|{meeting.attendeePW}|{name}|{role.name if hash_from_string else role}"
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
    from b3desk.models.bbb import BBB

    if waiting_room and not BBB(meeting.meetingID).is_running():
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
        db.session.add(meeting)
        db.session.commit()

    nickname = f"{fullname} - {fullname_suffix}" if fullname_suffix else fullname
    return (
        BBB(meeting.meetingID).prepare_request_to_join_bbb(meeting_role, nickname).url
    )


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


def create_bbb_meeting(meeting, user=None) -> bool:
    """Create a BBB room for a persistent meeting."""
    from b3desk.models.bbb import BBB
    from b3desk.models.meetings import pin_generation

    bbb = BBB(meeting.meetingID)
    if bbb.is_running():
        return False

    current_app.logger.info("Request BBB room creation %s %s", meeting.name, meeting.id)
    meeting.voiceBridge = (
        pin_generation() if not meeting.voiceBridge else meeting.voiceBridge
    )

    moderator_only_message = render_template(
        "meeting/signin_links.html",
        moderator_message=meeting.moderatorOnlyMessage,
        moderator_link_introduction=current_app.config[
            "QUICK_MEETING_MODERATOR_LINK_INTRODUCTION"
        ],
        moderator_signin_url=get_signin_url(meeting, Role.moderator),
        attendee_link_introduction=current_app.config[
            "QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION"
        ],
        attendee_signin_url=get_signin_url(meeting, Role.attendee),
    )

    meta_academy = user.mail_domain if user and user.mail_domain else None

    result = bbb.create(
        name=meeting.name,
        record=meeting.record,
        auto_start_recording=meeting.autoStartRecording,
        allow_start_stop_recording=meeting.allowStartStopRecording,
        webcams_only_for_moderator=meeting.webcamsOnlyForModerator,
        mute_on_start=meeting.muteOnStart,
        lock_settings_disable_cam=meeting.lockSettingsDisableCam,
        lock_settings_disable_mic=meeting.lockSettingsDisableMic,
        allow_mods_to_unmute_users=meeting.allowModsToUnmuteUsers,
        lock_settings_disable_private_chat=meeting.lockSettingsDisablePrivateChat,
        lock_settings_disable_public_chat=meeting.lockSettingsDisablePublicChat,
        lock_settings_disable_note=meeting.lockSettingsDisableNote,
        attendee_pw=meeting.attendeePW,
        moderator_pw=meeting.moderatorPW,
        welcome=meeting.welcome,
        max_participants=meeting.maxParticipants,
        logout_url=meeting.logoutUrl
        or current_app.config.get("MEETING_LOGOUT_URL", ""),
        duration=meeting.duration,
        voice_bridge=meeting.voiceBridge
        if current_app.config["ENABLE_PIN_MANAGEMENT"]
        else None,
        guest_policy=meeting.guestPolicy,
        presentation_upload_external_url=url_for(
            "meeting_files.file_picker", meeting=meeting, _external=True
        ),
        presentation_upload_external_description=current_app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        moderator_only_message=moderator_only_message,
        meta_academy=meta_academy,
        analytics_callback_url=current_app.config[
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
        ],
    )
    if not BBB.success(result):
        current_app.logger.warning("BBB room has not been properly created: %s", result)
        return False

    if meeting.files:
        bbb.send_meeting_files(meeting.files, meeting=meeting)

    if (
        current_app.config["ENABLE_PIN_MANAGEMENT"]
        and meeting.voiceBridge != result["voiceBridge"]
    ):
        current_app.logger.error(
            "Voice bridge seems managed by Scalelite or BBB, B3Desk database has different values: voice bridge sent '%s' received '%s'",
            meeting.voiceBridge,
            result["voiceBridge"],
        )

    return True


def create_bbb_quick_meeting(
    fake_id: str,
    user=None,
    is_mail_meeting: bool = False,
) -> bool:
    """Create a BBB room for a quick meeting."""
    from b3desk.models.bbb import BBB
    from b3desk.models.meetings import get_deterministic_password
    from b3desk.models.meetings import pin_generation

    meeting_id = f"meeting-vanish-{fake_id}--"
    name = current_app.config["QUICK_MEETING_DEFAULT_NAME"]
    moderator_pw = get_deterministic_password(fake_id, "moderator")
    attendee_pw = (
        None if is_mail_meeting else get_deterministic_password(fake_id, "attendee")
    )
    meta_academy = user.mail_domain if user and user.mail_domain else None

    bbb = BBB(meeting_id)
    if bbb.is_running():
        return False

    current_app.logger.info("Request BBB quick room creation %s %s", name, fake_id)

    voice_bridge = (
        pin_generation() if current_app.config["ENABLE_PIN_MANAGEMENT"] else None
    )

    if is_mail_meeting:
        expiration = str((datetime.now() + timedelta(weeks=1)).timestamp()).split(".")[
            0
        ]
        mail_signin_url = url_for(
            "join.signin_mail_meeting",
            meeting_fake_id=fake_id,
            expiration=expiration,
            hash_=get_mail_signin_hash(fake_id, expiration),
            _external=True,
        )
        moderator_only_message = render_template(
            "meeting/signin_mail_link.html",
            main_message=current_app.config["MAIL_MODERATOR_WELCOME_MESSAGE"],
            link=mail_signin_url,
        )
    else:

        def compute_hash(role: Role) -> str:
            s = f"{meeting_id}|{attendee_pw}|{name}|{role}"
            return hashlib.sha1(s.encode("utf-8")).hexdigest()

        moderator_signin_url = url_for(
            "join.signin_meeting",
            meeting_fake_id=fake_id,
            hash_=compute_hash(Role.moderator),
            role=Role.moderator,
            _external=True,
            _scheme=current_app.config["PREFERRED_URL_SCHEME"],
        )
        attendee_signin_url = url_for(
            "join.signin_meeting",
            meeting_fake_id=fake_id,
            hash_=compute_hash(Role.attendee),
            role=Role.attendee,
            _external=True,
            _scheme=current_app.config["PREFERRED_URL_SCHEME"],
        )
        moderator_only_message = render_template(
            "meeting/signin_links.html",
            moderator_message=current_app.config[
                "QUICK_MEETING_MODERATOR_WELCOME_MESSAGE"
            ],
            moderator_link_introduction=current_app.config[
                "QUICK_MEETING_MODERATOR_LINK_INTRODUCTION"
            ],
            moderator_signin_url=moderator_signin_url,
            attendee_link_introduction=current_app.config[
                "QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION"
            ],
            attendee_signin_url=attendee_signin_url,
        )

    logout_url = current_app.config["QUICK_MEETING_LOGOUT_URL"] or url_for(
        "public.index", _external=True
    )

    result = bbb.create(
        name=name,
        attendee_pw=attendee_pw,
        moderator_pw=moderator_pw,
        moderator_only_message=moderator_only_message,
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        logout_url=logout_url,
        voice_bridge=voice_bridge,
        meta_academy=meta_academy,
        analytics_callback_url=current_app.config[
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
        ],
    )
    if not BBB.success(result):
        current_app.logger.warning("BBB room has not been properly created: %s", result)
        return False

    return True
