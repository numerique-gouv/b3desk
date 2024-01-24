#!/bin/bash

# DB Migration
flask db upgrade &>> /var/log/flask-migrate.log

gunicorn --chdir /opt/bbb-visio --bind 0.0.0.0:5000 --log-level warning --access-logfile /var/log/gunicorn-access.log --error-logfile /var/log/gunicorn-error.log wsgi:app
