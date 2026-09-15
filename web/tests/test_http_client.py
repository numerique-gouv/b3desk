"""Temporary smoke test for the shared HTTP client plumbing."""

import httpx2
from b3desk import http_client


def test_http_client_is_lazy_and_shared(client_app):
    """The client is built once per process, on first use."""
    app = client_app.app
    assert "http_client" not in app.extensions

    with app.app_context():
        client = http_client()
        assert isinstance(client, httpx2.Client)
        assert client.timeout.read == 10
        assert http_client() is client
