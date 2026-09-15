#!/bin/bash

# DB Migration
flask db upgrade &>> /var/log/flask-migrate.log

gunicorn --config /opt/bbb-visio/gunicorn.conf.py wsgi:app
