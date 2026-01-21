import os
import secrets
import uuid
from datetime import date
from pathlib import Path

import filetype
import requests
from flask import Blueprint
from flask import abort
from flask import after_this_request
from flask import current_app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask_babel import lazy_gettext as _
from sqlalchemy import exc
from webdav3.exceptions import WebDavException
from werkzeug.utils import secure_filename

from b3desk.forms import MeetingFilesForm
from b3desk.models import db
from b3desk.models.bbb import BBB
from b3desk.models.meetings import AccessLevel
from b3desk.models.meetings import BaseMeetingFiles
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import get_meeting_file_hash
from b3desk.models.users import User
from b3desk.nextcloud import create_webdav_client
from b3desk.nextcloud import is_nextcloud_available
from b3desk.utils import check_oidc_connection

from .. import auth
from ..session import meeting_access_required
from ..session import user_needed

REQUEST_TIMEOUT = 10
bp = Blueprint("meeting_files", __name__)


@bp.route("/meeting/files/<meeting:meeting>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def edit_meeting_files(meeting: Meeting, user: User):
    """Display the meeting files management page."""
    form = MeetingFilesForm()

    if not current_app.config["FILE_SHARING"]:
        flash(_("Vous ne pouvez pas modifier cet élément"), "warning")
        return redirect(url_for("public.welcome"))

    g.is_nextcloud_available = is_nextcloud_available(
        user, verify=True, retry_on_auth_error=True
    )
    db.session.commit()

    return render_template(
        "meeting/filesform.html",
        meeting=meeting,
        form=form,
    )


@bp.route("/meeting/files/<meeting:meeting>", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def add_meeting_files(meeting: Meeting, user: User):
    """Add a file to a meeting from Nextcloud, URL, or file upload."""
    data = request.get_json()

    if data["from"] == "nextcloud":
        return add_meeting_file_nextcloud(data["value"], meeting.id)

    if data["from"] == "URL":
        return add_meeting_file_URL(data["value"], meeting.id)

    if data["from"] == "upload":
        return add_meeting_file_from_upload(secure_filename(data["value"]), meeting.id)

    return {"msg": "no file provided"}, 400


@bp.route("/meeting/files/<meeting:meeting>/")
@bp.route("/meeting/files/<meeting:meeting>/<int:file_id>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def download_meeting_files(meeting: Meeting, user: User, file_id=None):
    """Download a meeting file from URL or Nextcloud."""
    tmp_download_dir = current_app.config["TMP_DOWNLOAD_DIR"]
    Path(tmp_download_dir).mkdir(parents=True, exist_ok=True)
    tmp_name = os.path.join(tmp_download_dir, secrets.token_urlsafe(32))
    file_to_send = None

    for current_file in meeting.files:
        if current_file.id == file_id:
            file_to_send = current_file
            break

    if not file_to_send:
        return {"msg": "file not found"}, 404

    @after_this_request
    def cleanup(response):
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        return response

    if file_to_send.url:
        response = requests.get(file_to_send.url)
        with open(tmp_name, "wb") as f:
            f.write(response.content)
        return send_file(tmp_name, as_attachment=True, download_name=file_to_send.title)

    # get file from nextcloud WEBDAV and send it
    nc_available = is_nextcloud_available(user, verify=True, retry_on_auth_error=True)
    db.session.commit()
    if not nc_available:
        flash(
            _(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            ),
            "error",
        )
        return redirect(url_for("public.welcome"))

    client = create_webdav_client(user)
    client.download_sync(remote_path=file_to_send.nc_path, local_path=tmp_name)
    return send_file(tmp_name, as_attachment=True, download_name=file_to_send.title)


@bp.route("/meeting/files/<meetingfiles:meeting_file>/toggledownload", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@user_needed
def toggledownload(meeting_file: MeetingFiles, user: User):
    """Toggle the downloadable status of a meeting file."""
    if meeting_file.meeting.owner_id != user.id:
        abort(403)

    data = request.get_json()
    meeting_file.is_downloadable = data["value"]
    db.session.add(meeting_file)
    db.session.commit()

    return {"id": meeting_file.id}


def remove_uploaded_file(absolute_path):
    """Remove a file from the upload temporary directory."""
    os.remove(absolute_path)


def add_meeting_file_from_upload(title, meeting_id):
    """Upload a file to Nextcloud and associate it with a meeting."""
    upload_chunk_dir = os.path.join(current_app.config["UPLOAD_DIR"], "chunks")
    Path(upload_chunk_dir).mkdir(parents=True, exist_ok=True)
    upload_path = os.path.join(upload_chunk_dir, f"{g.user.id}-{meeting_id}-{title}")
    metadata = os.stat(upload_path)
    if int(metadata.st_size) > current_app.config["MAX_SIZE_UPLOAD"]:
        return {
            "msg": _(
                "Fichier {title} trop volumineux, ne pas dépasser {max_size}Mo"
            ).format(
                title=title,
                max_size=current_app.config["MAX_SIZE_UPLOAD"] // 1_000_000,
            )
        }, 413

    if (client := create_webdav_client(g.user)) is None:
        current_app.logger.warning(
            "WebDAV error: User %s has no credentials", g.user.id
        )
        return {
            "msg": _(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            )
        }, 503

    client.mkdir("visio-agents")  # does not fail if dir already exists
    nc_path = os.path.join("visio-agents", title)
    client.upload_sync(remote_path=nc_path, local_path=upload_path)
    remove_uploaded_file(upload_path)

    meeting_file = MeetingFiles(
        nc_path=nc_path,
        title=title,
        created_at=date.today(),
        meeting_id=meeting_id,
        owner=g.user,
    )

    try:
        db.session.add(meeting_file)
        db.session.commit()

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        try:
            client.clean(nc_path)
        except WebDavException as cleanup_error:
            current_app.logger.warning(
                "Failed to cleanup Nextcloud file %s: %s", nc_path, cleanup_error
            )
        return {"msg": _("Le fichier a déjà été mis en ligne")}, 409

    return {
        "title": meeting_file.short_title,
        "id": meeting_file.id,
        "created_at": meeting_file.created_at.strftime(
            current_app.config["TIME_FORMAT"]
        ),
    }


def add_meeting_file_URL(url, meeting_id):
    """Add a meeting file from an external URL."""
    title = url.rsplit("/", 1)[-1]

    try:
        metadata = requests.head(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as request_error:
        current_app.logger.warning(
            "URL file request failed for %s: %s", url, request_error
        )
        return {
            "msg": _(
                "Fichier {title} non disponible, veuillez vérifier l'URL proposée"
            ).format(title=title)
        }, 400

    if not metadata.ok:
        return {
            "msg": _(
                "Fichier {title} non disponible, veuillez vérifier l'URL proposée"
            ).format(title=title)
        }, 400

    content_length = metadata.headers.get("content-length")
    if content_length and int(content_length) > current_app.config["MAX_SIZE_UPLOAD"]:
        return {
            "msg": _(
                "Fichier {title} trop volumineux, ne pas dépasser {max_size}Mo"
            ).format(
                title=title,
                max_size=current_app.config["MAX_SIZE_UPLOAD"] // 1_000_000,
            )
        }, 413

    meeting_file = MeetingFiles(
        title=title,
        created_at=date.today(),
        meeting_id=meeting_id,
        url=url,
        owner=g.user,
    )

    try:
        db.session.add(meeting_file)
        db.session.commit()

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return {"msg": _("Le fichier a déjà été mis en ligne")}, 409

    return {
        "title": meeting_file.short_title,
        "id": meeting_file.id,
        "created_at": meeting_file.created_at.strftime(
            current_app.config["TIME_FORMAT"]
        ),
    }


def add_meeting_file_nextcloud(path, meeting_id):
    """Add a meeting file from a Nextcloud path."""
    if (client := create_webdav_client(g.user)) is None:
        return {
            "msg": _(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            )
        }, 503

    metadata = client.info(path)

    if int(metadata["size"]) > current_app.config["MAX_SIZE_UPLOAD"]:
        return {
            "msg": _(
                "Fichier {path} trop volumineux, ne pas dépasser {max_size}Mo"
            ).format(
                path=path,
                max_size=current_app.config["MAX_SIZE_UPLOAD"] // 1_000_000,
            )
        }, 413

    meeting_file = MeetingFiles(
        title=path.split("/")[-1],
        created_at=date.today(),
        meeting_id=meeting_id,
        nc_path=path,
        owner=g.user,
    )

    try:
        db.session.add(meeting_file)
        db.session.commit()

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return {"msg": _("Le fichier a déjà été mis en ligne")}, 409

    return {
        "title": meeting_file.short_title,
        "id": meeting_file.id,
        "created_at": meeting_file.created_at.strftime(
            current_app.config["TIME_FORMAT"]
        ),
    }


def create_external_meeting_file(path, owner, meeting_id=None):
    """Create an external meeting file record for a Nextcloud document."""
    return BaseMeetingFiles(
        title=path.split("/")[-1],
        meeting_id=meeting_id,
        nc_path=path,
        id=uuid.uuid4(),
        owner=owner,
    )


@bp.route("/meeting/files/<meeting:meeting>/upload", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def upload_file_chunks(meeting: Meeting, user: User):
    """Handle chunked file uploads."""
    file = request.files["dropzoneFiles"]
    upload_chunk_dir = os.path.join(current_app.config["UPLOAD_DIR"], "chunks")
    Path(upload_chunk_dir).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join(
        upload_chunk_dir, secure_filename(f"{user.id}-{meeting.id}-{file.filename}")
    )
    current_chunk = int(request.form["dzchunkindex"])

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        return {"msg": _("Le fichier a déjà été mis en ligne")}, 409

    try:
        with open(save_path, "ab") as f:
            f.seek(int(request.form["dzchunkbyteoffset"]))
            f.write(file.stream.read())

    except OSError:
        return {"msg": _("Erreur lors de l'écriture du fichier sur le disque")}, 500

    total_chunks = int(request.form["dztotalchunkcount"])

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        mimetype = filetype.guess(save_path)
        if (
            mimetype
            and mimetype.mime
            not in current_app.config["ALLOWED_MIME_TYPES_SERVER_SIDE"]
        ):
            os.remove(save_path)
            return {"msg": _("Type de fichier non autorisé")}, 400

        if os.path.getsize(save_path) != int(request.form["dztotalfilesize"]):
            os.remove(save_path)
            return {"msg": _("Erreur de taille du fichier")}, 400

    current_app.logger.debug(f"Wrote a chunk at {save_path}")
    return {"msg": "ok"}, 200


@bp.route("/meeting/files/delete", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def delete_meeting_file():
    """Delete a meeting file."""
    data = request.get_json()
    meeting_file_id = data["id"]
    meeting_file = db.session.get(MeetingFiles, meeting_file_id)
    if meeting_file is None:
        return {"id": data["id"], "msg": _("Fichier introuvable")}, 404

    if meeting_file.meeting.owner_id != g.user.id:
        return {
            "id": data["id"],
            "msg": _("Vous ne pouvez pas supprimer cet élément"),
        }, 403

    db.session.delete(meeting_file)
    db.session.commit()

    return {
        "id": data["id"],
        "msg": _("Fichier supprimé avec succès"),
    }


@bp.route("/meeting/<signed:bbb_meeting_id>/file-picker")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@user_needed
def file_picker(user: User, bbb_meeting_id: str):
    """Display the nextcloud file selector.

    This endpoint is used by BBB during the meetings.
    It is configurated by the 'presentationUploadExternalUrl' parameter on the creation request.
    """
    if BBB(bbb_meeting_id).is_running():
        nc_available = is_nextcloud_available(
            user, verify=True, retry_on_auth_error=True
        )
        db.session.commit()
        return render_template(
            "meeting/file_picker.html",
            bbb_meeting_id=bbb_meeting_id,
            is_nextcloud_available=nc_available,
        )
    flash(_("La réunion n'est pas en cours"), "error")
    return redirect(url_for("public.welcome"))


@bp.route(
    "/meeting/files/<signed:bbb_meeting_id>/file-picker-callback", methods=["POST"]
)
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@user_needed
def file_picker_callback(user: User, bbb_meeting_id: str):
    """Insert documents from Nextcloud into a running BBB meeting.

    This is called by the Nextcloud file picker when users select a document.
    This makes BBB download the document from the 'ncdownload' endpoint.
    """
    filenames = request.get_json()
    meeting_files = [
        create_external_meeting_file(filename, g.user) for filename in filenames
    ]
    BBB(bbb_meeting_id).send_meeting_files(meeting_files)

    return {"msg": "SUCCESS"}


@bp.route("/ncdownload/<token>/<user:user>/<path:ncpath>")
def ncdownload(token, user, ncpath):
    """Download a file from Nextcloud for BBB using a secure token."""
    current_app.logger.info("Service requesting file url %s", ncpath)
    if token != get_meeting_file_hash(user.id, ncpath):
        abort(404, "Bad token provided, no file matching")

    tmp_download_dir = current_app.config["TMP_DOWNLOAD_DIR"]
    Path(tmp_download_dir).mkdir(parents=True, exist_ok=True)
    uniqfile = str(uuid.uuid4())
    tmp_name = os.path.join(tmp_download_dir, uniqfile)

    if not is_nextcloud_available(user):
        return {
            "msg": _(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            )
        }, 503

    client = create_webdav_client(user)

    @after_this_request
    def cleanup(response):
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        return response

    mimetype = client.info(ncpath).get("content_type")
    client.download_sync(remote_path=ncpath, local_path=tmp_name)

    title = ncpath.split("/")[-1]
    return send_from_directory(
        tmp_download_dir, uniqfile, download_name=title, mimetype=mimetype
    )
