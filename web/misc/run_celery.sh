#!/bin/bash

exec celery --app tasks.celery worker --loglevel=info
