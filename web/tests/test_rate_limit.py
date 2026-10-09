from types import SimpleNamespace

import pytest
from b3desk import cache
from b3desk.rate_limit import visio_code_counter
from b3desk.rate_limit import visio_code_rate_limit
from flask import Flask
from flask import g
from redis.exceptions import ConnectionError


@pytest.fixture
def limited_app(monkeypatch):
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        CACHE_TYPE="SimpleCache",
        VISIO_CODE_RATE_LIMIT=2,
        VISIO_CODE_RATE_WINDOW=60,
    )
    cache.init_app(app)
    monkeypatch.setattr("b3desk.rate_limit.time.time", lambda: 120)

    @app.route("/check", methods=["POST"])
    @app.route("/join", methods=["POST"])
    @visio_code_rate_limit
    def check():
        return "ok"

    return app


def test_shared_budget_without_cookies(limited_app):
    client = limited_app.test_client(use_cookies=False)
    assert client.post("/check").status_code == 200
    assert client.post("/join").status_code == 200
    response = limited_app.test_client(use_cookies=False).post("/check")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert (
        client.post("/check", headers={"X-Forwarded-For": "192.0.2.1"}).status_code
        == 429
    )
    assert (
        client.post(
            "/check", environ_overrides={"REMOTE_ADDR": "192.0.2.1"}
        ).status_code
        == 200
    )


def test_window_expiration(limited_app, monkeypatch):
    client = limited_app.test_client()
    for _ in range(2):
        client.post("/check")
    monkeypatch.setattr("b3desk.rate_limit.time.time", lambda: 179)
    assert client.post("/check").headers["Retry-After"] == "1"
    monkeypatch.setattr("b3desk.rate_limit.time.time", lambda: 180)
    assert client.post("/check").status_code == 200


def test_user_budget_survives_ip_change_and_captcha_reset(limited_app):
    for ip in ("192.0.2.1", "192.0.2.2"):
        with limited_app.test_request_context(environ_base={"REMOTE_ADDR": ip}):
            g.user = SimpleNamespace(id=42)
            visio_code_counter("requests", increment=True)
            visio_code_counter("failures", increment=True)
            visio_code_counter("failures", reset=True)
            assert visio_code_counter("failures") == 0
    with limited_app.test_request_context(environ_base={"REMOTE_ADDR": "192.0.2.3"}):
        g.user = SimpleNamespace(id=42)
        assert visio_code_counter("requests") == 2


def test_redis_failure_blocks_verification(limited_app, monkeypatch):
    def unavailable(*args, **kwargs):
        raise ConnectionError("offline")

    monkeypatch.setattr(cache, "add", unavailable)
    assert limited_app.test_client().post("/check").status_code == 503


def test_production_requires_shared_redis(limited_app):
    limited_app.testing = False
    assert limited_app.test_client().post("/check").status_code == 503
