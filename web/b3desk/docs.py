"""Client for the Docs (La Suite numérique) external API."""

import requests
from flask import current_app

DOCS_API_TIMEOUT = 30


def _documents_url():
    base = current_app.config["DOCS_API_URL"].rstrip("/")
    return f"{base}/external_api/v1.0/documents/"


def create_document(access_token, filename, content, content_type="text/markdown"):
    """Create a Docs document from an uploaded file, owned by the token's user.

    Returns the created document as described by the Docs API.
    """
    response = requests.post(
        _documents_url(),
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": (filename, content, content_type)},
        timeout=DOCS_API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
