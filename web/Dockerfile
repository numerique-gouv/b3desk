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

COPY --from=root pyproject.toml uv.lock /opt/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --directory /opt --python /usr/local/bin/python

COPY misc/wsgi.py misc/gunicorn.py misc/run_webserver.sh /opt/bbb-visio/
COPY misc/job.cron /etc/cron.d/job
RUN chmod u+x /opt/bbb-visio/run_webserver.sh
COPY migrations /opt/bbb-visio/migrations
COPY b3desk /opt/bbb-visio/b3desk

WORKDIR /opt/bbb-visio/
ENTRYPOINT ["/opt/bbb-visio/run_webserver.sh"]
