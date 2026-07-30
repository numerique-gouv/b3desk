"""Client for the Docs (La Suite numérique) external API."""

import requests
from flask import current_app

DOCS_API_TIMEOUT = 30


def _base_url():
    return current_app.config["DOCS_API_URL"].rstrip("/")


def _documents_url():
    return f"{_base_url()}/external_api/v1.0/documents/"


def document_url(document_id):
    """Return the URL at which a user can open a Docs document."""
    return f"{_base_url()}/docs/{document_id}/"


def get_document(access_token, document_id):
    """Return a Docs document, or None when it is unreachable for the token's user."""
    response = requests.get(
        f"{_documents_url()}{document_id}/",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=DOCS_API_TIMEOUT,
    )
    if response.status_code in (403, 404):
        return None
    response.raise_for_status()
    return response.json()


def create_document(access_token, title):
    """Create an empty Docs document owned by the token's user.

    Returns the created document as described by the Docs API.
    """
    response = requests.post(
        _documents_url(),
        headers={"Authorization": f"Bearer {access_token}"},
        json={"title": title},
        timeout=DOCS_API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def create_child_document(
    access_token, parent_id, title, content, content_type="text/markdown"
):
    """Create a Docs document from an uploaded file, below an existing document.

    Docs names the document after the uploaded file, so the title is passed as the
    file name and carries no extension. Access rights are inherited from the parent.

    Returns the created document as described by the Docs API.
    """
    response = requests.post(
        f"{_documents_url()}{parent_id}/children/",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": (title, content, content_type)},
        timeout=DOCS_API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
