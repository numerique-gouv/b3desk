import hashlib
from datetime import datetime

from flask import current_app
from flask import render_template
from flask import url_for

from b3desk.endpoints.bbb_callback import get_recording_status_callback_url
from b3desk.models import db
from b3desk.models.roles import Role
from b3desk.nextcloud import is_nextcloud_available


def get_quick_meeting_secret_key(meeting, role: Role) -> str:
    name = meeting.name or str(current_app.config["QUICK_MEETING_DEFAULT_NAME"])
    s = f"{meeting.bbb_meeting_id}|{meeting.attendeePW}|{name}|{role}"
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def get_meeting_secret_key(meeting, role: Role) -> str:
    if meeting.quick:
        return get_quick_meeting_secret_key(meeting, role)

    from b3desk.models.meetings import MeetingSecretKey

    meeting_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == role.name,
        )
    ).one_or_none()
    return meeting_secret_key.secret_key if meeting_secret_key else None


def get_role(meeting, secret_key, user=None) -> Role | None:
    """Determine the meeting role based on hash and user."""
    if meeting.owner and meeting.owner == user:
        return Role.moderator

    if meeting.quick:
        if secret_key == get_quick_meeting_secret_key(meeting, Role.attendee):
            return Role.attendee
        if secret_key == get_quick_meeting_secret_key(meeting, Role.moderator):
            return Role.moderator
        if secret_key == get_quick_meeting_secret_key(meeting, Role.authenticated):
            return (
                Role.authenticated
                if current_app.config["OIDC_ATTENDEE_ENABLED"]
                else Role.attendee
            )
        return None

    from b3desk.models.meetings import MeetingSecretKey

    meeting_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.secret_key == secret_key,
        )
    ).one_or_none()
    if not meeting_secret_key:
        meeting_secret_key = next(
            (
                msk
                for msk in db.session.scalars(
                    db.select(MeetingSecretKey).where(
                        MeetingSecretKey.meeting_id == meeting.id
                    )
                )
                if secret_key in msk.legacy_secret_keys
            ),
            None,
        )
    if not meeting_secret_key:
        return None
    role = Role[meeting_secret_key.role]
    if role == Role.authenticated and not current_app.config["OIDC_ATTENDEE_ENABLED"]:
        return Role.attendee
    return role


def get_join_url(
    meeting,
    meeting_role: Role,
    fullname,
    fullname_suffix="",
    seconds_before_refresh=None,
    waiting_room=True,
):
    """Return the URL of the BBB meeting URL if available, and the URL of the b3desk 'waiting_meeting' if it is not ready."""
    from b3desk.models.bbb import BBB

    if waiting_room and not BBB(meeting.bbb_meeting_id).is_running():
        return url_for(
            "join.waiting_meeting",
            meeting_id=meeting.id,
            secret_key=get_meeting_secret_key(meeting, meeting_role),
            fullname=fullname,
            fullname_suffix=fullname_suffix,
            seconds_before_refresh=seconds_before_refresh,
        )

    if not meeting.quick:
        meeting.last_connection_utc_datetime = datetime.now()
        db.session.add(meeting)
        db.session.commit()

    nickname = f"{fullname} - {fullname_suffix}" if fullname_suffix else fullname
    return (
        BBB(meeting.bbb_meeting_id)
        .prepare_request_to_join_bbb(meeting_role, nickname)
        .url
    )


def create_signin_url(meeting, meeting_role: Role, secret_key: str):
    """Generate the sign-in URL for a specific role."""
    return url_for(
        "join.signin_meeting",
        meeting_id=meeting.id,
        secret_key=secret_key,
        role=meeting_role,
        _external=True,
        _scheme=current_app.config["PREFERRED_URL_SCHEME"],
    )


def create_bbb_meeting(meeting, user=None) -> bool:
    """Create a BBB room for a persistent meeting."""
    from b3desk.models.bbb import BBB

    bbb = BBB(meeting.bbb_meeting_id)
    if bbb.is_running():
        return False

    if user:
        is_nextcloud_available(user, verify=True, retry_on_auth_error=True)
        db.session.commit()

    current_app.logger.info("Request BBB room creation %s %s", meeting.name, meeting.id)

    moderator_only_message = render_template(
        "meeting/signin_links.html",
        moderator_message=meeting.moderatorOnlyMessage,
        visio_code=meeting.visio_code,
        moderator_link_introduction=current_app.config[
            "QUICK_MEETING_MODERATOR_LINK_INTRODUCTION"
        ],
        moderator_signin_url=meeting.moderator_url,
        attendee_link_introduction=current_app.config[
            "QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION"
        ],
        attendee_signin_url=meeting.attendee_url,
    )
    meta_bbb_recording_ready_url = get_recording_status_callback_url()

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
            "meeting_files.file_picker",
            bbb_meeting_id=meeting.bbb_meeting_id,
            _external=True,
        ),
        presentation_upload_external_description=current_app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        moderator_only_message=moderator_only_message,
        meta_academy=meta_academy,
        analytics_callback_url=current_app.config[
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
        ],
        meta_bbb_recording_ready_url=meta_bbb_recording_ready_url,
        ai_summary=meeting.ai_summary_enabled,
        file_sharing=meeting.owner.can_use_file_sharing,
    )

    current_app.logger.info(
        "BBB persistent meeting room %s creation result: %s",
        meeting.bbb_meeting_id,
        result,
    )

    if not BBB.success(result):
        return False

    if meeting.files:
        bbb.send_meeting_files(meeting.files)

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


def create_bbb_quick_meeting(meeting, user=None) -> bool:
    """Create a BBB room for a quick meeting."""
    from b3desk.models.bbb import BBB
    from b3desk.models.meetings import get_deterministic_password
    from b3desk.models.meetings import pin_generation

    name = str(current_app.config["QUICK_MEETING_DEFAULT_NAME"])
    moderator_pw = get_deterministic_password(meeting.id, "moderator")
    meta_academy = user.mail_domain if user and user.mail_domain else None

    bbb = BBB(meeting.bbb_meeting_id)
    if bbb.is_running():
        return False

    current_app.logger.info("Request BBB quick room creation %s %s", name, meeting.id)

    voice_bridge = (
        pin_generation() if current_app.config["ENABLE_PIN_MANAGEMENT"] else None
    )

    moderator_signin_url = create_signin_url(
        meeting, Role.moderator, get_quick_meeting_secret_key(meeting, Role.moderator)
    )
    attendee_signin_url = create_signin_url(
        meeting, Role.attendee, get_quick_meeting_secret_key(meeting, Role.attendee)
    )
    moderator_only_message = render_template(
        "meeting/signin_links.html",
        visio_code=None,
        moderator_message=current_app.config["QUICK_MEETING_MODERATOR_WELCOME_MESSAGE"],
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
        attendee_pw=meeting.attendeePW,
        moderator_pw=moderator_pw,
        moderator_only_message=moderator_only_message,
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        logout_url=logout_url,
        voice_bridge=voice_bridge,
        meta_academy=meta_academy,
        analytics_callback_url=current_app.config[
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
        ],
        presentation_upload_external_url=url_for(
            "meeting_files.file_picker",
            bbb_meeting_id=meeting.bbb_meeting_id,
            _external=True,
        ),
        presentation_upload_external_description=current_app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
    )

    current_app.logger.info(
        "BBB vanish meeting room %s creation result: %s", meeting.bbb_meeting_id, result
    )

    return BBB.success(result)
