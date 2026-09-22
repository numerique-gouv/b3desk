FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/
RUN \
  apt update && \
  apt --yes upgrade && \
  apt install --yes --no-install-recommends gcc curl libc6-dev libpq-dev && \
  rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/opt/.venv/bin:$PATH"

COPY --from=root pyproject.toml uv.lock README.md /opt/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --directory /opt --python /usr/local/bin/python

# The sources are laid out under the module-root declared in pyproject.toml,
# installed into the virtualenv, then dropped: --no-editable copies the code
# into site-packages, so the image carries the application and importlib can
# read its version.
COPY b3desk /opt/web/b3desk
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --directory /opt --python /usr/local/bin/python && \
    rm -rf /opt/web

COPY misc/wsgi.py misc/gunicorn.conf.py misc/run_webserver.sh /opt/bbb-visio/
COPY misc/job.cron /etc/cron.d/job
COPY migrations /opt/bbb-visio/migrations
COPY translations /opt/bbb-visio/translations

RUN pybabel compile --directory /opt/bbb-visio/translations
RUN chmod u+x /opt/bbb-visio/run_webserver.sh

WORKDIR /opt/bbb-visio/
ENTRYPOINT ["/opt/bbb-visio/run_webserver.sh"]
