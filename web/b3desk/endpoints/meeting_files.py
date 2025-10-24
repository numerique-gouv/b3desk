import hashlib
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
from webdav3.client import Client as webdavClient
from webdav3.exceptions import WebDavException
from werkzeug.utils import secure_filename

from b3desk.forms import MeetingFilesForm
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import MeetingFilesExternal
from b3desk.models.users import User
from b3desk.nextcloud import nextcloud_healthcheck
from b3desk.utils import check_oidc_connection

from .. import auth
from ..session import get_current_user
from ..session import meeting_owner_needed

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

    if owner.has_nc_credentials:
        nextcloud_healthcheck(owner)

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
    try:
        dav_user = {
            "nc_locator": owner.nc_locator,
            "nc_login": owner.nc_login,
            "nc_token": owner.nc_token,
        }
        options = {
            "webdav_root": f"/remote.php/dav/files/{dav_user['nc_login']}/",
            "webdav_hostname": dav_user["nc_locator"],
            "webdav_verbose": True,
            "webdav_token": dav_user["nc_token"],
        }
        client = webdavClient(options)
        kwargs = {
            "remote_path": current_file.nc_path,
            "local_path": f"{tmp_name}",
        }
        client.download_sync(**kwargs)
        return send_file(tmp_name, as_attachment=True, download_name=current_file.title)

    except WebDavException as exception:
        owner.disable_nextcloud()
        current_app.logger.warning(
            "webdav call encountered following exception : %s", exception
        )
        flash("Le fichier ne semble pas accessible", "error")
        return redirect(url_for("public.welcome"))


# called by NextcloudfilePicker when documents should be added to a running room:
@bp.route("/meeting/files/<meeting:meeting>/insertDocuments", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def insertDocuments(meeting: Meeting):
    """Insert documents from Nextcloud into a running BBB meeting."""
    from flask import request

    filenames = request.get_json()
    secret_key = current_app.config["SECRET_KEY"]

    xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
    xml_end = " </module></modules>"
    xml_mid = ""
    # @FIX We ONLY send the documents that have been uploaded NOW, not ALL of them for this meetingid ;)
    for filename in filenames:
        id = add_external_meeting_file_nextcloud(filename, meeting.id)
        filehash = hashlib.sha1(
            f"{secret_key}-1-{id}-{secret_key}".encode()
        ).hexdigest()
        current_app.logger.info(
            "Call insert document BigBlueButton API in running room for %s", filename
        )
        url = url_for(
            "meeting_files.ncdownload",
            isexternal=1,
            mfid=id,
            mftoken=filehash,
            filename=filename,
            _external=True,
        )
        xml_mid += f"<document url='{url}' filename='{filename}' />"

    bbb_endpoint = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
    xml = xml_beg + xml_mid + xml_end
    params = {"meetingID": meeting.meetingID}
    request = requests.Request(
        "POST",
        "{}/{}".format(current_app.config["BIGBLUEBUTTON_ENDPOINT"], "insertDocument"),
        params=params,
    )
    pr = request.prepare()
    bigbluebutton_secret = current_app.config["BIGBLUEBUTTON_SECRET"]
    s = "{}{}".format(
        pr.url.replace("?", "").replace(
            current_app.config["BIGBLUEBUTTON_ENDPOINT"] + "/", ""
        ),
        bigbluebutton_secret,
    )
    params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()
    requests.post(
        f"{bbb_endpoint}/insertDocument",
        headers={"Content-Type": "application/xml"},
        data=xml,
        params=params,
    )
    return jsonify(status=200, msg="SUCCESS")


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
    meeting_file.save()

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

    meeting_file = MeetingFiles.query.get(data["id"])
    meeting_file.is_default = True

    if actual_default_file:
        actual_default_file.save()
    meeting_file.save()

    return jsonify(status=200, id=data["id"])


def remove_dropzone_file(absolutePath):
    """Remove a file from the dropzone temporary directory."""
    os.remove(absolutePath)


# called when a file has been uploaded : send it to nextcloud
def add_meeting_file_dropzone(title, meeting_id, is_default):
    """Upload a dropzone file to Nextcloud and associate it with a meeting."""
    user = get_current_user()
    # should be in /tmp/visioagent/dropzone/USER_ID-TITLE
    DROPZONE_DIR = os.path.join(current_app.config["UPLOAD_DIR"], "dropzone")
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    dropzone_path = os.path.join(DROPZONE_DIR, f"{user.id}-{meeting_id}-{title}")
    metadata = os.stat(dropzone_path)
    if int(metadata.st_size) > current_app.config["MAX_SIZE_UPLOAD"]:
        return jsonify(
            status=500,
            isfrom="dropzone",
            msg=f"Fichier {title} TROP VOLUMINEUX, ne pas dépasser 20Mo",
        )

    options = {
        "webdav_root": f"/remote.php/dav/files/{user.nc_login}/",
        "webdav_hostname": user.nc_locator,
        "webdav_verbose": True,
        "webdav_token": user.nc_token,
    }
    try:
        client = webdavClient(options)
        client.mkdir("visio-agents")  # does not fail if dir already exists
        # Upload resource
        nc_path = os.path.join("/visio-agents/" + title)
        kwargs = {
            "remote_path": nc_path,
            "local_path": dropzone_path,
        }
        client.upload_sync(**kwargs)

        meeting_file = MeetingFiles(
            nc_path=nc_path,
            title=title,
            created_at=date.today(),
            meeting_id=meeting_id,
        )

    except WebDavException as exception:
        user.disable_nextcloud()
        current_app.logger.warning("WebDAV error: %s", exception)
        return jsonify(
            status=500, isfrom="dropzone", msg="La connexion avec Nextcloud est rompue"
        )

    try:
        # test for is_default-file absence at the latest time possible
        meeting = db.session.get(Meeting, meeting_id)
        meeting_file.is_default = len(meeting.files) == 0 and not meeting.default_file
        meeting_file.save()

        # file has been associated AND uploaded to nextcloud, we can safely remove it from visio-agent tmp directory
        remove_dropzone_file(dropzone_path)
        return jsonify(
            status=200,
            isfrom="dropzone",
            isDefault=is_default,
            title=meeting_file.short_title,
            id=meeting_file.id,
            created_at=meeting_file.created_at.strftime(
                current_app.config["TIME_FORMAT"]
            ),
        )

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return jsonify(
            status=500, isfrom="dropzone", msg="Le fichier a déjà été mis en ligne"
        )


def add_meeting_file_URL(url, meeting_id, is_default):
    """Add a meeting file from an external URL."""
    title = url.rsplit("/", 1)[-1]

    # test MAX_SIZE_UPLOAD for 20Mo
    metadata = requests.head(url)
    if not metadata.ok:
        return jsonify(
            status=404,
            isfrom="url",
            msg=f"Fichier {title} NON DISPONIBLE, veuillez vérifier l'URL proposée",
        )

    if int(metadata.headers["content-length"]) > current_app.config["MAX_SIZE_UPLOAD"]:
        return jsonify(
            status=500,
            isfrom="url",
            msg=f"Fichier {title} TROP VOLUMINEUX, ne pas dépasser 20Mo",
        )

    meeting_file = MeetingFiles(
        title=title,
        created_at=date.today(),
        meeting_id=meeting_id,
        url=url,
        is_default=is_default,
    )
    requests.get(url)

    try:
        meeting_file.save()
        return jsonify(
            status=200,
            isfrom="url",
            isDefault=is_default,
            title=meeting_file.short_title,
            id=meeting_file.id,
            created_at=meeting_file.created_at.strftime(
                current_app.config["TIME_FORMAT"]
            ),
        )

    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return jsonify(
            status=500, isfrom="url", msg="Le fichier a déjà été mis en ligne"
        )


def add_meeting_file_nextcloud(path, meeting_id, is_default):
    """Add a meeting file from a Nextcloud path."""
    user = get_current_user()

    options = {
        "webdav_root": f"/remote.php/dav/files/{user.nc_login}/",
        "webdav_hostname": user.nc_locator,
        "webdav_verbose": True,
        "webdav_token": user.nc_token,
    }
    try:
        client = webdavClient(options)
        metadata = client.info(path)

    except WebDavException:
        user.disable_nextcloud()
        return jsonify(
            status=500,
            isfrom="nextcloud",
            msg="La connexion avec Nextcloud semble rompue",
        )

    if int(metadata["size"]) > current_app.config["MAX_SIZE_UPLOAD"]:
        return jsonify(
            status=500,
            isfrom="nextcloud",
            msg=f"Fichier {path} TROP VOLUMINEUX, ne pas dépasser 20Mo",
        )

    meeting_file = MeetingFiles(
        title=path.split("/")[-1],
        created_at=date.today(),
        meeting_id=meeting_id,
        nc_path=path,
        is_default=is_default,
    )

    try:
        meeting_file.save()
        return jsonify(
            status=200,
            isfrom="nextcloud",
            isDefault=is_default,
            title=meeting_file.short_title,
            id=meeting_file.id,
            created_at=meeting_file.created_at.strftime(
                current_app.config["TIME_FORMAT"]
            ),
        )
    except exc.SQLAlchemyError as exception:
        current_app.logger.error("SQLAlchemy error: %s", exception)
        return jsonify(
            status=500, isfrom="nextcloud", msg="Le fichier a déjà été mis en ligne"
        )


def add_external_meeting_file_nextcloud(path, meeting_id):
    """Create an external meeting file record for a Nextcloud document."""
    externalMeetingFile = MeetingFilesExternal(
        title=path, meeting_id=meeting_id, nc_path=path
    )
    externalMeetingFile.save()
    return externalMeetingFile.id


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
        return make_response(("Le fichier a déjà été mis en ligne", 500))

    try:
        with open(save_path, "ab") as f:
            f.seek(int(request.form["dzchunkbyteoffset"]))
            f.write(file.stream.read())

    except OSError:
        return make_response(
            ("Not sure why, but we couldn't write the file to disk", 500)
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
    user = get_current_user()
    data = request.get_json()
    meeting_file_id = data["id"]
    meeting_file = MeetingFiles.query.get(meeting_file_id)
    cur_meeting = Meeting.query.get(meeting_file.meeting_id)

    if cur_meeting.user_id != user.id:
        return jsonify(
            status=500, id=data["id"], msg="Vous ne pouvez pas supprimer cet élément"
        )

    db.session.delete(meeting_file)
    db.session.commit()
    new_default_id = None
    if meeting_file.is_default:
        cur_meeting = Meeting.query.get(meeting_file.meeting_id)
        if len(cur_meeting.files) > 0:
            cur_meeting.files[0].is_default = True
            new_default_id = cur_meeting.files[0].id
            cur_meeting.save()

    return jsonify(
        status=200,
        newDefaultId=new_default_id,
        id=data["id"],
        msg="Fichier supprimé avec succès",
    )


# draft for insertDocument calls to BBB API
# @TODO: can we remove this def entirely?
@bp.route("/insertDoc/<token>")
def insertDoc(token):
    """Insert a document into a BBB meeting using a token (draft implementation)."""
    # select good file from token
    # get file through NC credentials - HOW POSSIBLE ?
    # return file as response to BBB server

    meeting_file = MeetingFiles.query.filter_by(download_hash=token).one()
    secret_key = current_app.config["SECRET_KEY"]
    if (
        meeting_file
        or meeting_file.token
        != hashlib.sha1(
            f"{secret_key}{meeting_file.id}{secret_key}".encode()
        ).hexdigest()
    ):
        make_response("NOT OK", 500)

    params = {"meetingID": meeting_file.meeting.meetingID}
    action = "insertDocument"
    req = requests.Request(
        "POST",
        "{}/{}".format(current_app.config["BIGBLUEBUTTON_ENDPOINT"], action),
        params=params,
    )
    headers = {"Content-Type": "application/xml"}
    pr = req.prepare()
    bigbluebutton_secret = current_app.config["BIGBLUEBUTTON_SECRET"]
    s = "{}{}".format(
        pr.url.replace("?", "").replace(
            current_app.config["BIGBLUEBUTTON_ENDPOINT"] + "/", ""
        ),
        bigbluebutton_secret,
    )
    params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()

    # xml now use
    url = url_for(
        "meeting_files.ncdownload",
        isexternal=0,
        mfid=meeting_file.id,
        mftoken=meeting_file.download_hash,
        filename=meeting_file.title,
        _external=True,
    )
    xml = f"<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'><document url='{url}' filename='{meeting_file.title}' /> </module></modules>"

    current_app.logger.info(
        "Call insert document BigBlueButton API for %s", meeting_file.title
    )
    requests.post(
        f"{current_app.config['BIGBLUEBUTTON_ENDPOINT']}/insertDocument",
        data=xml,
        headers=headers,
        params=params,
    )

    return make_response("ok", 200)


@bp.route("/ncdownload/<int:isexternal>/<mfid>/<mftoken>")
@bp.route("/ncdownload/<int:isexternal>/<mfid>/<mftoken>/<filename>")
def ncdownload(isexternal, mfid, mftoken, filename=None):
    """Download a file from Nextcloud for BBB using a secure token."""
    current_app.logger.info("Service requesting file url %s", filename)
    secret_key = current_app.config["SECRET_KEY"]
    # select good file from token
    # get file through NC credentials - HOW POSSIBLE ?
    # return file as response to BBB server
    # isexternal tells if the file has been chosen earlier from the visio-agent interface (0) or if it has been uploaded from BBB itself (1)
    model = MeetingFiles if isexternal == 0 else MeetingFilesExternal
    meeting_file = model.query.filter_by(id=mfid).one_or_none()

    if not meeting_file:
        abort(404, "Bad token provided, no file matching")

    # the hash token consist of the sha1 of "secret key - 0/1 (internal/external) - id in the DB - secret key"
    if (
        mftoken
        != hashlib.sha1(
            f"{secret_key}-{isexternal}-{mfid}-{secret_key}".encode()
        ).hexdigest()
    ):
        abort(404, "Bad token provided, no file matching")

    # download the file using webdavClient from the Nextcloud to a temporary folder (that will need cleaning)
    options = {
        "webdav_root": f"/remote.php/dav/files/{meeting_file.meeting.user.nc_login}/",
        "webdav_hostname": meeting_file.meeting.user.nc_locator,
        "webdav_verbose": True,
        "webdav_token": meeting_file.meeting.user.nc_token,
    }
    TMP_DOWNLOAD_DIR = current_app.config["TMP_DOWNLOAD_DIR"]
    Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    uniqfile = str(uuid.uuid4())
    tmp_name = f"{TMP_DOWNLOAD_DIR}{uniqfile}"

    try:
        client = webdavClient(options)
        mimetype = client.info(meeting_file.nc_path).get("content_type")
        client.download_sync(remote_path=meeting_file.nc_path, local_path=tmp_name)

    except WebDavException:
        meeting_file.meeting.user.disable_nextcloud()
        return jsonify(status=500, msg="La connexion avec Nextcloud semble rompue")

    # send the downloaded file to the BBB:
    return send_from_directory(
        TMP_DOWNLOAD_DIR, uniqfile, download_name=meeting_file.title, mimetype=mimetype
    )
