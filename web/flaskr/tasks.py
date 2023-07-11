import os

import requests
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL")

celery = Celery("tasks")
celery.conf.broker_url = f"redis://{REDIS_URL}"
celery.conf.result_backend = f"redis://{REDIS_URL}"


@celery.task(name="background_upload")
def background_upload(endpoint, xml, params):
    requests.post(
        endpoint,
        headers={"Content-Type": "application/xml"},
        data=xml,
        params=params,
    )
    print(f"adding background files endpoint:{endpoint} xml:{xml} params:{params}")
    return True
