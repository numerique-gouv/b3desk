import logging

from flask import Blueprint
from flask import current_app
from flask import request
from flask import url_for
from joserfc import jwt
from joserfc.errors import BadSignatureError
from joserfc.errors import DecodeError
from joserfc.jwk import OctKey

from b3desk import cache
from b3desk import csrf
from b3desk.models.meetings import get_meeting_from_bbb_meeting_id
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


@csrf.exempt
@bp.route("/bbb-callback/recording_status", methods=["POST"])
def recording_status():
    """Handle BBB callback when a recording format is available.

    BBB triggers this callback once per rendered format (presentation, video, ...).
    To send a single notification covering all formats, the first callback for a
    given record_id schedules a Celery task with a ``RECORDING_NOTIFICATION_DELAY``
    countdown; subsequent callbacks for the same record_id within that window are
    acknowledged (200) but do nothing. The task re-queries BBB at expiry to fetch
    the final list of available formats before sending the mail.

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

    cache_key = f"recording_notification_scheduled:{bbb_recording_id}"
    if cache.get(cache_key):
        logger.info(
            "Recording notification already scheduled for %s, ignoring callback",
            bbb_recording_id,
        )
        return "", 200

    delay = current_app.config["RECORDING_NOTIFICATION_DELAY"]
    cache.set(cache_key, True, timeout=7 * 24 * 3600)
    send_recording_notification.apply_async(
        args=[meeting.id, bbb_recording_id],
        countdown=delay,
    )
    logger.info(
        "Recording notification scheduled for meeting %s in %ss (record=%s)",
        meeting.name,
        delay,
        bbb_recording_id,
    )
    return "", 200
