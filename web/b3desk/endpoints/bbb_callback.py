import logging

from flask import Blueprint
from flask import current_app
from flask import request
from flask import url_for
from joserfc import jwt
from joserfc.errors import BadSignatureError
from joserfc.errors import DecodeError
from joserfc.jwk import OctKey

from b3desk import csrf
from b3desk.models.meetings import get_meeting_from_bbb_meetingID
from b3desk.utils import send_available_recording_notification_mail

bp = Blueprint("bbb-callback", __name__)

logger = logging.getLogger("bbb-callback")


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
    """Handle BBB callback when a recording is available."""
    from b3desk.models.bbb import BBB

    key = OctKey.import_key(current_app.config["BIGBLUEBUTTON_SECRET"].encode())

    try:
        token = jwt.decode(request.form["signed_parameters"], key)
    except (BadSignatureError, DecodeError):
        logger.error(
            "The shared secret does not match %s %s", BadSignatureError, DecodeError
        )
        return "", 401

    bbb_meeting_id = token.claims["meeting_id"]
    bbb_recording_id = token.claims["record_id"]

    meeting = get_meeting_from_bbb_meetingID(bbb_meeting_id)
    if not meeting:
        return "", 410

    bbb = BBB(bbb_meeting_id)
    try:
        recordings = bbb.get_recordings(bbb_recording_id=bbb_recording_id)
        recording_url = recordings[0]["playbacks"]["presentation"]["url"]
        recording_name = recordings[0]["name"]
        recording_start = recordings[0]["start_date"].strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error("BBB failed to find recording: %s", e)
        return "", 500

    send_available_recording_notification_mail(
        meeting, recording_url, recording_name, recording_start
    )
    logger.info(
        "BBB recording is available for meeting %s: %s", meeting.name, recording_url
    )
    logger.warning(recordings[0]["start_date"])
    return "", 200
