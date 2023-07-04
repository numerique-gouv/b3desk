FROM python:3.8-bullseye

# Install.
RUN \
  apt update && \
  apt -y upgrade && \
  apt install -y gcc libpq-dev

COPY requirements.app.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY misc/wsgi.py misc/gunicorn.py misc/run_webserver.sh /opt/bbb-visio/
COPY misc/delete_uploaded_files.cron /etc/cron.d/delete_uploaded_files
RUN chmod u+x /opt/bbb-visio/run_webserver.sh
COPY migrations /opt/bbb-visio/migrations
COPY instance/config.py /opt/bbb-visio/instance/config.py
COPY flaskr /opt/bbb-visio/flaskr

WORKDIR /opt/bbb-visio/
ENTRYPOINT ["/opt/bbb-visio/run_webserver.sh"]
