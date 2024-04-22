import os

import requests
from celery import Celery
from celery.utils.log import get_task_logger

REDIS_URL = os.environ.get("REDIS_URL")

celery = Celery("tasks")
celery.conf.broker_url = f"redis://{REDIS_URL}"
celery.conf.result_backend = f"redis://{REDIS_URL}"

logger = get_task_logger(__name__)


@celery.task(name="background_upload")
def background_upload(endpoint, xml):
    response = requests.post(
        endpoint,
        headers={"Content-Type": "application/xml"},
        data=xml,
    )
    logger.info("BBB API request %s: xml:%s", endpoint, xml)
    logger.info("BBB API response %s", response.text)
    return True
