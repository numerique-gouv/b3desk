import logging
from datetime import datetime

import requests
from flask import Blueprint
from flask import current_app
from flask import request
from flask import url_for
from joserfc import jwt
from joserfc.errors import BadSignatureError
from joserfc.errors import DecodeError
from joserfc.errors import JoseError
from joserfc.jwk import OctKey

from b3desk import cache
from b3desk import csrf
from b3desk.models import db
from b3desk.models.meetings import MeetingSession
from b3desk.models.meetings import get_meeting_from_bbb_meeting_id
from b3desk.tasks import RECORDING_CACHE_TTL
from b3desk.tasks import recording_notified_key
from b3desk.tasks import recording_scheduled_key
from b3desk.tasks import send_recording_notification

bp = Blueprint("bbb-callback", __name__)

logger = logging.getLogger(__name__)


def get_recording_status_callback_url():
    """Get the URL of the callback used by BBB to notify that the registration is available."""
    return url_for(
        "bbb-callback.recording_status",
        _external=True,
        _scheme=current_app.config["PREFERRED_URL_SCHEME"],
    )


def get_analytics_callback_url():
    """Get the URL of the callback used by BBB to send analytics data."""
    return url_for(
        "bbb-callback.analytics_callback",
        _external=True,
        _scheme=current_app.config["PREFERRED_URL_SCHEME"],
    )


def _parse_bbb_datetime(value):
    """Parse a BBB analytics ISO-8601 timestamp into naive local time."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone().replace(tzinfo=None)
    except (TypeError, ValueError):
        logger.warning("Could not parse BBB analytics timestamp %r", value)
        return None


@csrf.exempt
@bp.route("/bbb-callback/analytics", methods=["POST"])
def analytics_callback():
    """Handle BBB's analytics callback (``meta_analytics-callback-url``)."""
    auth_header = request.headers.get("Authorization", "")
    token_value = auth_header.removeprefix("Bearer ").strip()
    if not token_value:
        logger.error("Missing bearer token in analytics callback")
        return "", 401

    key = OctKey.import_key(current_app.config["BIGBLUEBUTTON_SECRET"].encode())

    try:
        # BBB signs this callback with HS512
        jwt.decode(token_value, key, algorithms=["HS512"])
    except JoseError as e:
        logger.error("Invalid signature on analytics callback: %s", e)
        return "", 401

    payload = request.get_json(silent=True, force=True) or {}
    bbb_meeting_id = payload.get("meeting_id")
    meeting = (
        get_meeting_from_bbb_meeting_id(bbb_meeting_id) if bbb_meeting_id else None
    )

    if not meeting:
        logger.warning(
            "Analytics callback for unknown or missing meetingID=%r", bbb_meeting_id
        )
    else:
        session = (
            MeetingSession.query.filter_by(meeting_id=meeting.id, ended_at=None)
            .order_by(MeetingSession.started_at.desc())
            .first()
        )
        if session:
            data = payload.get("data") or {}
            started_at = _parse_bbb_datetime(data.get("start"))
            if started_at:
                session.started_at = started_at
            session.ended_at = _parse_bbb_datetime(data.get("finish")) or datetime.now()
            attendees = data.get("attendees")
            if isinstance(attendees, list):
                session.participant_count = len(attendees)
            db.session.commit()
            logger.info(
                "Analytics callback closed session for meeting %s (meetingID=%s)",
                meeting.name,
                bbb_meeting_id,
            )
        else:
            logger.warning(
                "Analytics callback received for meeting %s (meetingID=%s) "
                "but no open session found",
                meeting.name,
                bbb_meeting_id,
            )

    analytics_url = current_app.config["BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"]
    if analytics_url:
        try:
            requests.post(
                analytics_url,
                data=request.get_data(),
                headers={
                    "Content-Type": request.content_type or "application/json",
                    "Authorization": auth_header,
                },
                timeout=current_app.config["BIGBLUEBUTTON_REQUEST_TIMEOUT"],
            )
        except requests.RequestException as e:
            logger.error(
                "Failed to relay analytics callback to %s: %s", analytics_url, e
            )

    return "", 200


@csrf.exempt
@bp.route("/bbb-callback/recording_status", methods=["POST"])
def recording_status():
    """Handle BBB callback when a recording format is available.

    BBB triggers this callback once per rendered format (presentation, video, ...).
    To send a single notification covering all formats, the first callback for a
    given record_id schedules two deadline tasks: one at
    ``RECORDING_NOTIFICATION_MIN_DELAY`` that unlocks sending, and one at
    ``RECORDING_NOTIFICATION_MAX_DELAY`` that sends whatever is ready as a safety
    net. Subsequent callbacks re-check the available formats and send as soon as
    all expected ones are present (once the minimum delay has elapsed). The
    ``send_recording_notification`` task re-queries BBB each time and
    guards against duplicate mails with an atomic cache flag.

    Returns 410 on definitively invalid payloads to stop BBB retries
    (BBB only stops retrying on 2xx and 410, per the API documentation).
    """
    signed_parameters = request.form.get("signed_parameters")
    if not signed_parameters:
        logger.error("Missing 'signed_parameters' in callback payload")
        return "", 410

    key = OctKey.import_key(current_app.config["BIGBLUEBUTTON_SECRET"].encode())

    try:
        token = jwt.decode(signed_parameters, key)
    except (BadSignatureError, DecodeError) as e:
        logger.error("Invalid signature on callback: %s", e)
        return "", 401

    bbb_meeting_id = token.claims.get("meeting_id")
    bbb_recording_id = token.claims.get("record_id")
    if not bbb_meeting_id or not bbb_recording_id:
        logger.error(
            "Missing claims in callback token: meeting_id=%r record_id=%r",
            bbb_meeting_id,
            bbb_recording_id,
        )
        return "", 410

    meeting = get_meeting_from_bbb_meeting_id(bbb_meeting_id)
    if not meeting:
        return "", 410

    already_matched = MeetingSession.query.filter_by(
        meeting_id=meeting.id, recording_id=bbb_recording_id
    ).first()
    if not already_matched:
        session = (
            MeetingSession.query.filter_by(meeting_id=meeting.id, recording_id=None)
            .order_by(MeetingSession.started_at.desc())
            .first()
        )
        if session:
            session.recording_id = bbb_recording_id
            db.session.commit()

    if cache.get(recording_notified_key(bbb_recording_id)):
        logger.info(
            "Recording notification already sent for %s, ignoring callback",
            bbb_recording_id,
        )
        return "", 200

    is_first_callback = cache.add(
        recording_scheduled_key(bbb_recording_id), True, timeout=RECORDING_CACHE_TTL
    )
    if is_first_callback:
        min_delay = current_app.config["RECORDING_NOTIFICATION_MIN_DELAY"]
        max_delay = current_app.config["RECORDING_NOTIFICATION_MAX_DELAY"]
        send_recording_notification.apply_async(
            args=[meeting.id, bbb_recording_id],
            kwargs={"is_min_deadline": True},
            countdown=min_delay,
        )
        send_recording_notification.apply_async(
            args=[meeting.id, bbb_recording_id],
            kwargs={"force": True},
            countdown=max_delay,
        )
        logger.info(
            "Recording notification scheduled for meeting %s (record=%s): "
            "min=%ss max=%ss",
            meeting.name,
            bbb_recording_id,
            min_delay,
            max_delay,
        )
    else:
        send_recording_notification.delay(meeting.id, bbb_recording_id)
        logger.info(
            "Recording callback for %s: re-checking expected formats",
            bbb_recording_id,
        )
    return "", 200
