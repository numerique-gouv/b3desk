import os

import requests
from celery import Celery
from celery.utils.log import get_task_logger
from flask import current_app

from b3desk import cache
from b3desk.models import db
from b3desk.utils import send_available_recording_notification_mail

REDIS_URL = os.environ.get("REDIS_URL")
DEBUG = os.environ.get("FLASK_DEBUG")

celery = Celery("tasks")
celery.conf.broker_url = f"redis://{REDIS_URL}"
celery.conf.result_backend = f"redis://{REDIS_URL}"

logger = get_task_logger(__name__)

# Recording notifications are tracked across callbacks through these cache keys,
# kept long enough to cover the whole rendering window of a recording.
RECORDING_CACHE_TTL = 7 * 24 * 3600


def recording_scheduled_key(bbb_recording_id):
    """Cache key flagging that the deadline tasks were scheduled for a recording."""
    return f"recording_notification_scheduled:{bbb_recording_id}"


def recording_min_reached_key(bbb_recording_id):
    """Cache key flagging that the minimum delay has elapsed for a recording."""
    return f"recording_notification_min_reached:{bbb_recording_id}"


def recording_notified_key(bbb_recording_id):
    """Cache key flagging that the notification mail was sent for a recording."""
    return f"recording_notification_sent:{bbb_recording_id}"


@celery.task(name="background_upload")
def background_upload(endpoint, xml):
    """Celery task to upload XML documents to BigBlueButton API in background."""
    logger.info("BBB API request %s: xml:%s", endpoint, xml)

    session = requests.Session()
    if DEBUG:  # pragma: no cover
        # In local development environment, BBB is not served as https
        session.verify = False

    response = session.post(
        endpoint,
        headers={"Content-Type": "application/xml"},
        data=xml,
    )

    logger.info("BBB API response %s", response.text)
    return True


@celery.task(name="send_recording_notification")
def send_recording_notification(
    meeting_id, bbb_recording_id, force=False, is_min_deadline=False
):
    """Send the recording notification mail once the expected formats are ready.

    Triggered on every BBB callback and by the min/max deadline tasks. Sends a
    single mail when all expected formats are available (after the minimum
    delay), or unconditionally when the maximum-delay safety net fires
    (``force``). A ``notified`` cache flag, claimed atomically before sending,
    prevents concurrent callbacks and deadline tasks from sending duplicates.
    """
    from b3desk.models.bbb import BBB
    from b3desk.models.meetings import Meeting

    if cache.get(recording_notified_key(bbb_recording_id)):
        return

    meeting = db.session.get(Meeting, meeting_id)
    if not meeting:
        logger.warning(
            "Meeting %s no longer exists, skipping recording notification",
            meeting_id,
        )
        return

    if is_min_deadline:
        cache.set(
            recording_min_reached_key(bbb_recording_id),
            True,
            timeout=RECORDING_CACHE_TTL,
        )
    min_reached = is_min_deadline or bool(
        cache.get(recording_min_reached_key(bbb_recording_id))
    )

    bbb = BBB(meeting.meetingID)
    recordings = BBB.get_recordings.uncached(bbb, bbb_recording_id=bbb_recording_id)
    if not recordings:
        logger.warning(
            "No recording returned by BBB for %s, skipping notification",
            bbb_recording_id,
        )
        return

    try:
        recording = recordings[0]
        playbacks = recording["playbacks"]
        recording_name = recording["name"]
        recording_start = recording["start_date"].isoformat()
    except (KeyError, AttributeError) as e:
        logger.error(
            "Unexpected BBB recording structure for %s: %s", bbb_recording_id, e
        )
        return

    expected = set(current_app.config["RECORDING_EXPECTED_FORMATS"])
    if meeting.ai_summary_enabled:
        expected.add("ai-summary")
    else:
        expected.discard("ai-summary")
    complete = expected.issubset(playbacks.keys())

    if not (force or (min_reached and complete)):
        return

    # Claim the notification atomically so a concurrent callback or deadline task
    # cannot send a duplicate mail for the same recording.
    if not cache.add(
        recording_notified_key(bbb_recording_id), True, timeout=RECORDING_CACHE_TTL
    ):
        return

    send_available_recording_notification_mail(
        meeting, playbacks, recording_name, recording_start
    )
