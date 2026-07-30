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
from flask_babel import format_datetime
from flask_babel import lazy_gettext as _

from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import RecordingDocument
from b3desk.utils import check_oidc_connection

from .. import auth
from .. import oauth
from ..docs import create_child_document
from ..docs import create_document
from ..docs import get_document
from ..session import meeting_access_required

bp = Blueprint("docs", __name__)

DOCS_SESSION_KEY = "docs_push_target"
SUMMARY_DOWNLOAD_TIMEOUT = 30


def _recording_summary(meeting, recording_id):
    """Return the title and Markdown AI summary URL of a recording, if any."""
    for recording in meeting.bbb.get_recordings(bbb_recording_id=recording_id):
        if recording.get("recordID") != recording_id:
            continue
        title = recording.get("name") or format_datetime(
            recording["start_date"], "yyyy-MM-dd HH:mm:ss"
        )
        return title, recording.get("playbacks", {}).get("ai-summary", {}).get("md")
    return None, None


def _meeting_document_id(access_token, meeting):
    """Return the Docs document gathering the meeting summaries, creating it if needed.

    The document is recreated when it became unreachable, either because its owner
    deleted it or because the meeting changed hands.
    """
    if meeting.docs_document_id and get_document(
        access_token, meeting.docs_document_id
    ):
        return meeting.docs_document_id

    meeting.docs_document_id = create_document(access_token, meeting.name)["id"]
    return meeting.docs_document_id


@bp.route(
    "/meeting/<meeting:meeting>/recordings/<recording_id>/to-docs", methods=["POST"]
)
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required()
def push_recording_to_docs(meeting: Meeting, recording_id, user):
    """Start the ProConnect flow used to store a recording summary in Docs."""
    if meeting.owner != user:
        abort(403)

    if meeting.docs_document_id_for_recording(recording_id):
        return redirect(url_for("meetings.show_meeting_recording", meeting=meeting))

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

    recording_id = target["recording_id"]
    title, summary_url = _recording_summary(meeting, recording_id)
    if not summary_url:
        flash(_("Aucun compte rendu à enregistrer dans Docs."), "error")
        return redirect(recordings_url)

    access_token = token["access_token"]
    try:
        summary = requests.get(summary_url, timeout=SUMMARY_DOWNLOAD_TIMEOUT)
        summary.raise_for_status()
        parent_id = _meeting_document_id(access_token, meeting)
        # The parent is persisted before the upload, so a failing upload does not
        # leave an orphan document behind in Docs.
        db.session.commit()
        document = create_child_document(
            access_token, parent_id, title, summary.content
        )
    except requests.RequestException:
        db.session.rollback()
        flash(_("L’enregistrement du compte rendu dans Docs a échoué."), "error")
        return redirect(recordings_url)

    db.session.add(
        RecordingDocument(
            meeting=meeting,
            recording_id=recording_id,
            document_id=document["id"],
        )
    )
    db.session.commit()

    flash(_("Le compte rendu a été enregistré dans Docs."), "success")
    return redirect(recordings_url)
