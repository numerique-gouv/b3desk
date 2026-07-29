import os

import requests
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from flask import current_app

from b3desk import cache
from b3desk.models import db
from b3desk.models.meetings import clean_db_and_delete_meeting
from b3desk.models.meetings import get_inactive_meetings_to_delete
from b3desk.models.meetings import get_inactive_meetings_to_inform
from b3desk.models.users import clean_db_and_delete_user
from b3desk.models.users import get_inactive_users_to_delete
from b3desk.utils.mailing import send_available_recording_notification_mail
from b3desk.utils.mailing import send_mail_before_meeting_deletion

REDIS_URL = os.environ.get("REDIS_URL")
DEBUG = os.environ.get("FLASK_DEBUG")

celery = Celery("tasks")
celery.conf.broker_url = f"redis://{REDIS_URL}"
celery.conf.result_backend = f"redis://{REDIS_URL}"
celery.conf.beat_schedule = {
    "delete-old-meetings-every-day-at-3-am": {
        "task": "delete-old-meetings",
        "schedule": crontab(minute=00, hour=3),
    },
    "inform-owner-before-meeting-deletion-every-day-at-4-am": {
        "task": "inform-owner-before-meeting-deletion",
        "schedule": crontab(minute=00, hour=4),
    },
    "delete-old-users-every-day-at-3-30-am": {
        "task": "delete-old-users",
        "schedule": crontab(minute=30, hour=3),
    },
}

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

    bbb = BBB(meeting.bbb_meeting_id)
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


@celery.task(name="delete-old-meetings")
def delete_old_meetings():
    """Celery cron task to delete expired meetings from database."""
    logger.info("Celery cron task: delete_old_meetings started")
    from b3desk import create_app

    app = create_app()
    with app.app_context():
        meetings_to_delete = get_inactive_meetings_to_delete()

        if meetings_to_delete:
            logger.info(
                "Celery cron task: %d expired meetings to delete",
                len(meetings_to_delete),
            )
        for meeting in meetings_to_delete:
            _, category = clean_db_and_delete_meeting(meeting, celery_cron=True)
            if category == "success":
                logger.info(
                    "Celery cron task: %s id:%s named:%s deleted",
                    "shadow_meeting" if meeting.is_shadow else "meeting",
                    meeting.id,
                    meeting.name,
                )
        logger.info("Celery cron task: delete_old_meetings ended")


@celery.task(name="inform-owner-before-meeting-deletion")
def inform_owner_before_meeting_deletion():
    """Celery cron task to inform meeting owner before meeting deletion."""
    logger.info("Celery cron task: inform_owner_before_meeting_deletion started")
    from b3desk import create_app

    app = create_app()
    with app.app_context():
        meetings_to_inform = get_inactive_meetings_to_inform()

        if meetings_to_inform:
            logger.info(
                "Celery cron task: %d meetings expire soon", len(meetings_to_inform)
            )
        for meeting, delay in meetings_to_inform:
            send_mail_before_meeting_deletion(meeting, delay)
            logger.info(
                "Celery cron task: %s id:%s named:%s informed (%d day(s) left)",
                "shadow_meeting" if meeting.is_shadow else "meeting",
                meeting.id,
                meeting.name,
                delay,
            )
        logger.info("Celery cron task: inform_owner_before_meeting_deletion ended")


@celery.task(name="delete-old-users")
def delete_old_users():
    """Celery cron task to delete expired meetings from database."""
    logger.info("Celery cron task: delete_old_users started")
    from b3desk import create_app

    app = create_app()
    with app.app_context():
        users_to_delete = get_inactive_users_to_delete()

        if users_to_delete:
            logger.info(
                "Celery cron task: %d expired user accounts to delete",
                len(users_to_delete),
            )
        for user in users_to_delete:
            if clean_db_and_delete_user(user):
                logger.info(
                    "Celery cron task: user %s, id %s, email %s, deleted",
                    user.fullname,
                    user.id,
                    user.email,
                )
            else:
                logger.error(
                    "Celery cron task: user not deleted: %s, id %s, email %s",
                    user.fullname,
                    user.id,
                    user.email,
                )
        logger.info("Celery cron task: delete_old_users ended")
