#!/bin/bash

celery --app tasks.celery worker --loglevel=info
