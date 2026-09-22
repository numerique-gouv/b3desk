"""Gunicorn configuration for the b3desk web container.

The gthread worker replaces the default sync one because almost all of the
request time is spent waiting on BigBlueButton, Nextcloud and captchetat: a
blocking call then holds a single thread instead of a whole process.

Under gthread the arbiter timeout is a liveness check, not a request deadline,
since the worker event loop keeps notifying the arbiter while requests run in
the thread pool. It is set above the longest legitimate request — a file
download, bounded by DOWNLOAD_MAX_DURATION — because a worker recycling itself
after max_requests drains under that timeout rather than under graceful_timeout.

The control socket path is pinned so that "docker exec web gunicornc status"
works without depending on the environment of the exec session.
"""

import os

bind = "0.0.0.0:5000"
chdir = "/opt/bbb-visio"

workers = int(os.environ.get("WEB_CONCURRENCY", 4))
worker_class = "gthread"
threads = int(os.environ.get("WEB_THREADS", 4))
worker_tmp_dir = "/dev/shm"
control_socket = "/run/gunicorn.ctl"

timeout = 90
graceful_timeout = 30
keepalive = 5

max_requests = 1000
max_requests_jitter = 100

accesslog = "/var/log/gunicorn-access.log"
errorlog = "/var/log/gunicorn-error.log"
loglevel = os.environ.get("WEB_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'
