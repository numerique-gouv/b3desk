import os

import requests
from celery import Celery
from celery.utils.log import get_task_logger

from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.utils import send_available_recording_notification_mail

REDIS_URL = os.environ.get("REDIS_URL")
DEBUG = os.environ.get("FLASK_DEBUG")

celery = Celery("tasks")
celery.conf.broker_url = f"redis://{REDIS_URL}"
celery.conf.result_backend = f"redis://{REDIS_URL}"

logger = get_task_logger(__name__)


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
    meeting_id, recording_url, recording_name, recording_start
):
    """Send the recording-available notification mail for the given meeting."""
    meeting = db.session.get(Meeting, meeting_id)
    if not meeting:
        logger.warning(
            "Meeting %s no longer exists, skipping recording notification",
            meeting_id,
        )
        return
    send_available_recording_notification_mail(
        meeting, recording_url, recording_name, recording_start
    )
