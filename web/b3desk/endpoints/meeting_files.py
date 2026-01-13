import os
import secrets
import uuid
from datetime import date
from pathlib import Path

import filetype
import requests
from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import g
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask import url_for
from flask_babel import lazy_gettext as _
from sqlalchemy import exc
from werkzeug.utils import secure_filename

from b3desk.forms import MeetingFilesForm
from b3desk.models import db
from b3desk.models.bbb import BBB
from b3desk.models.meetings import BaseMeetingFiles
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import get_meeting_file_hash
from b3desk.models.users import User
from b3desk.nextcloud import check_nextcloud_connection
from b3desk.nextcloud import create_webdav_client
from b3desk.nextcloud import is_nextcloud_available
from b3desk.utils import check_oidc_connection

from .. import auth
from ..session import meeting_owner_needed
from ..session import user_needed

bp = Blueprint("meeting_files", __name__)


@bp.route("/meeting/files/<meeting:meeting>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def edit_meeting_files(meeting: Meeting, owner: User):
    """Display the meeting files management page."""
    form = MeetingFilesForm()

    if not current_app.config["FILE_SHARING"]:
        flash(_("Vous ne pouvez pas modifier cet élément"), "warning")
        return redirect(url_for("public.welcome"))

    g.is_nextcloud_available = check_nextcloud_connection(
        owner, retry_on_auth_error=True
    )

    return render_template(
        "meeting/filesform.html",
        meeting=meeting,
        form=form,
    )


@bp.route("/meeting/files/<meeting:meeting>", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def add_meeting_files(meeting: Meeting, owner: User):
    """Add a file to a meeting from Nextcloud, URL, or dropzone upload."""
    data = request.get_json()
    is_default = False
    if len(meeting.files) == 0:
        is_default = True

    if data["from"] == "nextcloud":
        return add_meeting_file_nextcloud(data["value"], meeting.id, is_default)

    if data["from"] == "URL":
        return add_meeting_file_URL(data["value"], meeting.id, is_default)

    # This is called by the JS after uploading a file on the 'add_dropzone_files'
    # TODO: do everything in one single request?
    if data["from"] == "dropzone":
        return add_meeting_file_dropzone(
            secure_filename(data["value"]), meeting.id, is_default
        )

    return jsonify("no file provided")


@bp.route("/meeting/files/<meeting:meeting>/")
@bp.route("/meeting/files/<meeting:meeting>/<int:file_id>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def download_meeting_files(meeting: Meeting, owner: User, file_id=None):
    """Download a meeting file from URL or Nextcloud."""
    TMP_DOWNLOAD_DIR = current_app.config["TMP_DOWNLOAD_DIR"]
    Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    tmp_name = f"{current_app.config['TMP_DOWNLOAD_DIR']}{secrets.token_urlsafe(32)}"
    file_to_send = None

    for current_file in meeting.files:
        if current_file.id == file_id:
            file_to_send = current_file
            break

    if not file_to_send:
        return jsonify(status=404, msg="file not found")

    if current_file.url:
        response = requests.get(current_file.url)
        open(tmp_name, "wb").write(response.content)
        return send_file(tmp_name, as_attachment=True, download_name=current_file.title)

    # get file from nextcloud WEBDAV and send it
    if (client := create_webdav_client(owner)) is None:
        current_app.logger.warning("User %s has no Webdav credentials", owner.id)
        flash(
            _(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            ),
            "error",
        )
        return redirect(url_for("public.welcome"))

    client.download_sync(remote_path=current_file.nc_path, local_path=tmp_name)
    return send_file(tmp_name, as_attachment=True, download_name=current_file.title)


@bp.route("/meeting/files/<meeting:meeting>/toggledownload", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def toggledownload(meeting: Meeting, owner: User):
    """Toggle the downloadable status of a meeting file."""
    data = request.get_json()
    meeting_file = db.session.get(MeetingFiles, data["id"])
    if not meeting_file:
        abort(404)

    meeting_file.is_downloadable = data["value"]
    db.session.add(meeting_file)
    db.session.commit()

    return jsonify(status=200, id=data["id"])


@bp.route("/meeting/files/<meeting:meeting>/default", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def set_meeting_default_file(meeting: Meeting, owner: User):
    """Set a file as the default file for a meeting."""
    data = request.get_json()

    actual_default_file = meeting.default_file
    if actual_default_file:
        actual_default_file.is_default = False
        db.session.add(actual_default_file)

    meeting_file = MeetingFiles.query.get(data["id"])
    meeting_file.is_default = True
    db.session.add(meeting_file)
    db.session.commit()

    return jsonify(status=200, id=data["id"])


def remove_dropzone_file(absolutePath):
    """Remove a file from the dropzone temporary directory."""
    os.remove(absolutePath)


# called when a file has been uploaded : send it to nextcloud
def add_meeting_file_dropzone(title, meeting_id, is_default):
    """Upload a dropzone file to Nextcloud and associate it with a meeting."""
    # should be in /tmp/visioagent/dropzone/USER_ID-TITLE
    DROPZONE_DIR = os.path.join(current_app.config["UPLOAD_DIR"], "dropzone")
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    dropzone_path = os.path.join(DROPZONE_DIR, f"{g.user.id}-{meeting_id}-{title}")
    metadata = os.stat(dropzone_path)
    if int(metadata.st_size) > current_app.config["MAX_SIZE_UPLOAD"]:
        return jsonify(
            status=500,
            msg=_("Fichier {title} TROP VOLUMINEUX, ne pas dépasser 20Mo").format(
                title=title
            ),
        )

    if (client := create_webdav_client(g.user)) is None:
        current_app.logger.warning(
            "WebDAV error: User %s has no credentials", g.user.id
        )
        return jsonify(
            status=500,
            msg=_(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            ),
        )

    client.mkdir("visio-agents")  # does not fail if dir already exists
    nc_path = os.path.join("visio-agents" + title)
    client.upload_sync(remote_path=nc_path, local_path=dropzone_path)

    meeting_file = MeetingFiles(
        nc_path=nc_path,
        title=title,
        created_at=date.today(),
        meeting_id=meeting_id,
        owner=g.user,
    )

    try:
        # test for is_default-file absence at the latest time possible
        meeting = db.session.get(Meeting, meeting_id)
        meeting_file.is_default = len(meeting.files) == 0 and not meeting.default_file
        db.session.add(meeting_file)
        db.session.commit()

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return jsonify(status=500, msg=_("Le fichier a déjà été mis en ligne"))

    # file has been associated AND uploaded to nextcloud, we can safely remove it from visio-agent tmp directory
    remove_dropzone_file(dropzone_path)
    return jsonify(
        status=200,
        isDefault=is_default,
        title=meeting_file.short_title,
        id=meeting_file.id,
        created_at=meeting_file.created_at.strftime(current_app.config["TIME_FORMAT"]),
    )


def add_meeting_file_URL(url, meeting_id, is_default):
    """Add a meeting file from an external URL."""
    title = url.rsplit("/", 1)[-1]

    # test MAX_SIZE_UPLOAD for 20Mo
    metadata = requests.head(url)
    if not metadata.ok:
        return jsonify(
            status=404,
            msg=_(
                "Fichier {title} NON DISPONIBLE, veuillez vérifier l'URL proposée"
            ).format(title=title),
        )

    if int(metadata.headers["content-length"]) > current_app.config["MAX_SIZE_UPLOAD"]:
        return jsonify(
            status=500,
            msg=_("Fichier {title} TROP VOLUMINEUX, ne pas dépasser 20Mo").format(
                title=title
            ),
        )

    meeting_file = MeetingFiles(
        title=title,
        created_at=date.today(),
        meeting_id=meeting_id,
        url=url,
        is_default=is_default,
        owner=g.user,
    )
    requests.get(url)

    try:
        db.session.add(meeting_file)
        db.session.commit()

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return jsonify(status=500, msg=_("Le fichier a déjà été mis en ligne"))

    return jsonify(
        status=200,
        isDefault=is_default,
        title=meeting_file.short_title,
        id=meeting_file.id,
        created_at=meeting_file.created_at.strftime(current_app.config["TIME_FORMAT"]),
    )


def add_meeting_file_nextcloud(path, meeting_id, is_default):
    """Add a meeting file from a Nextcloud path."""
    if (client := create_webdav_client(g.user)) is None:
        return jsonify(
            status=500,
            msg=_(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            ),
        )

    metadata = client.info(path)

    if int(metadata["size"]) > current_app.config["MAX_SIZE_UPLOAD"]:
        return jsonify(
            status=500,
            msg=_("Fichier {path} TROP VOLUMINEUX, ne pas dépasser 20Mo").format(
                path=path
            ),
        )

    meeting_file = MeetingFiles(
        title=path.split("/")[-1],
        created_at=date.today(),
        meeting_id=meeting_id,
        nc_path=path,
        is_default=is_default,
        owner=g.user,
    )

    try:
        db.session.add(meeting_file)
        db.session.commit()

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return jsonify(status=500, msg=_("Le fichier a déjà été mis en ligne"))

    return jsonify(
        status=200,
        isDefault=is_default,
        title=meeting_file.short_title,
        id=meeting_file.id,
        created_at=meeting_file.created_at.strftime(current_app.config["TIME_FORMAT"]),
    )


def create_external_meeting_file(path, owner, meeting_id=None):
    """Create an external meeting file record for a Nextcloud document."""
    externalMeetingFile = BaseMeetingFiles(
        title=path.split("/")[-1],
        meeting_id=meeting_id,
        nc_path=path,
        id=uuid.uuid4(),
        owner=owner,
    )
    return externalMeetingFile


# for dropzone multiple files uploading at once
@bp.route("/meeting/files/<meeting:meeting>/dropzone", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def add_dropzone_files(meeting: Meeting, owner: User):
    """Handle chunked file uploads from dropzone."""
    file = request.files["dropzoneFiles"]
    # for dropzone chunk file by file validation
    # shamelessly taken from https://stackoverflow.com/questions/44727052/handling-large-file-uploads-with-flask
    DROPZONE_DIR = os.path.join(current_app.config["UPLOAD_DIR"], "dropzone")
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join(
        DROPZONE_DIR, secure_filename(f"{owner.id}-{meeting.id}-{file.filename}")
    )
    current_chunk = int(request.form["dzchunkindex"])

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response((str(_("Le fichier a déjà été mis en ligne")), 500))

    try:
        with open(save_path, "ab") as f:
            f.seek(int(request.form["dzchunkbyteoffset"]))
            f.write(file.stream.read())

    except OSError:
        return make_response(
            (str(_("Erreur lors de l'écriture du fichier sur le disque")), 500)
        )

    total_chunks = int(request.form["dztotalchunkcount"])

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        mimetype = filetype.guess(save_path)
        if mimetype.mime not in current_app.config["ALLOWED_MIME_TYPES_SERVER_SIDE"]:
            return make_response(("Filetype not allowed", 500))
        if os.path.getsize(save_path) != int(request.form["dztotalfilesize"]):
            return make_response(("Size mismatch", 500))

    current_app.logger.debug(f"Wrote a chunk at {save_path}")
    return make_response(("Chunk upload successful", 200))


@bp.route("/meeting/files/delete", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def delete_meeting_file():
    """Delete a meeting file and reassign default if necessary."""
    data = request.get_json()
    meeting_file_id = data["id"]
    meeting_file = MeetingFiles.query.get(meeting_file_id)
    if meeting_file is None:
        return jsonify(status=404, id=data["id"], msg=_("Fichier introuvable"))

    if meeting_file.meeting.user_id != g.user.id:
        return jsonify(
            status=500, id=data["id"], msg=_("Vous ne pouvez pas supprimer cet élément")
        )

    db.session.delete(meeting_file)
    db.session.commit()
    new_default_id = None
    if meeting_file.is_default:
        if len(meeting_file.meeting.files) > 0:
            meeting_file.meeting.files[0].is_default = True
            new_default_id = meeting_file.meeting.files[0].id
            db.session.commit()

    return jsonify(
        status=200,
        newDefaultId=new_default_id,
        id=data["id"],
        msg=_("Fichier supprimé avec succès"),
    )


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
        nc_available = is_nextcloud_available() and check_nextcloud_connection(user)
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

    return jsonify(status=200, msg="SUCCESS")


@bp.route("/ncdownload/<token>/<user:user>/<path:ncpath>")
def ncdownload(token, user, ncpath):
    """Download a file from Nextcloud for BBB using a secure token."""
    current_app.logger.info("Service requesting file url %s", ncpath)
    if token != get_meeting_file_hash(user.id, ncpath):
        abort(404, "Bad token provided, no file matching")

    # TODO: clean the temporary directory
    TMP_DOWNLOAD_DIR = current_app.config["TMP_DOWNLOAD_DIR"]
    Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    uniqfile = str(uuid.uuid4())
    tmp_name = f"{TMP_DOWNLOAD_DIR}{uniqfile}"

    if (client := create_webdav_client(user)) is None:
        return jsonify(
            status=500,
            msg=_(
                "Le service de fichiers est temporairement indisponible. "
                "Veuillez réessayer dans quelques minutes."
            ),
        )

    mimetype = client.info(ncpath).get("content_type")
    client.download_sync(remote_path=ncpath, local_path=tmp_name)

    title = ncpath.split("/")[-1]
    return send_from_directory(
        TMP_DOWNLOAD_DIR, uniqfile, download_name=title, mimetype=mimetype
    )
