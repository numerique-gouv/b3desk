# +----------------------------------------------------------------------------+
# | B3DESK                                                                  |
# +----------------------------------------------------------------------------+
#
#   This program is free software: you can redistribute it and/or modify it
# under the terms of the European Union Public License 1.2 version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
import requests
from authlib.integrations.flask_client import OAuthError
from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import redirect
from flask import session
from flask import url_for
from flask_babel import lazy_gettext as _

from b3desk.models import db
from b3desk.models.meetings import AccessLevel
from b3desk.models.meetings import Meeting
from b3desk.utils import check_oidc_connection

from .. import auth
from .. import oauth
from ..docs import create_document
from ..session import meeting_access_required

bp = Blueprint("docs", __name__)

DOCS_SESSION_KEY = "docs_push_target"
SUMMARY_DOWNLOAD_TIMEOUT = 30


def _summary_markdown_url(meeting, recording_id):
    """Return the URL of the Markdown AI summary for a recording, if any."""
    for recording in meeting.bbb.get_recordings(bbb_recording_id=recording_id):
        if recording.get("recordID") == recording_id:
            return recording.get("playbacks", {}).get("ai-summary", {}).get("md")
    return None


@bp.route(
    "/meeting/<meeting:meeting>/recordings/<recording_id>/to-docs", methods=["POST"]
)
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def push_recording_to_docs(meeting: Meeting, recording_id, user):
    """Start the ProConnect flow used to store a recording summary in Docs."""
    session[DOCS_SESSION_KEY] = {
        "meeting_id": meeting.id,
        "recording_id": recording_id,
    }
    params = {}
    idp_hint = current_app.config.get("DOCS_IDP_HINT")
    if idp_hint:
        params["idp_hint"] = idp_hint
    return oauth.docs.authorize_redirect(
        current_app.config["DOCS_REDIRECT_URI"], **params
    )


@bp.route("/docs_callback")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def docs_callback():
    """Receive the ProConnect authorization code and create the Docs document."""
    target = session.pop(DOCS_SESSION_KEY, None)
    if not target:
        abort(400)

    meeting = db.session.get(Meeting, target["meeting_id"])
    if meeting is None:
        abort(404)

    recordings_url = url_for("meetings.show_meeting_recording", meeting=meeting)

    try:
        token = oauth.docs.authorize_access_token()
    except OAuthError:
        flash(_("La connexion à Docs a échoué."), "error")
        return redirect(recordings_url)

    summary_url = _summary_markdown_url(meeting, target["recording_id"])
    if not summary_url:
        flash(_("Aucun compte rendu à enregistrer dans Docs."), "error")
        return redirect(recordings_url)

    try:
        summary = requests.get(summary_url, timeout=SUMMARY_DOWNLOAD_TIMEOUT)
        summary.raise_for_status()
        create_document(token["access_token"], f"{meeting.name}.md", summary.content)
    except requests.RequestException:
        flash(_("L’enregistrement du compte rendu dans Docs a échoué."), "error")
        return redirect(recordings_url)

    flash(_("Le compte rendu a été enregistré dans Docs."), "success")
    return redirect(recordings_url)
