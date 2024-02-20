# +----------------------------------------------------------------------------+
# | BBB-VISIO                                                                  |
# +----------------------------------------------------------------------------+
#
#   This program is free software: you can redistribute it and/or modify it
# under the terms of the European Union Public License 1.2 version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
import hashlib
import os
import secrets
import uuid
from datetime import date
from datetime import datetime
from pathlib import Path

import filetype
import requests
from b3desk.forms import EndMeetingForm
from b3desk.forms import JoinMailMeetingForm
from b3desk.forms import JoinMeetingAsRoleForm
from b3desk.forms import JoinMeetingForm
from b3desk.forms import MeetingFilesForm
from b3desk.forms import MeetingForm
from b3desk.forms import MeetingWithRecordForm
from b3desk.forms import RecordingForm
from b3desk.forms import ShowMeetingForm
from b3desk.models import db
from b3desk.models.meetings import get_mail_meeting
from b3desk.models.meetings import get_meeting_from_meeting_id_and_user_id
from b3desk.models.meetings import get_quick_meeting_from_user_and_random_string
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import MeetingFilesExternal
from b3desk.models.users import get_or_create_user
from b3desk.models.users import User
from flask import abort
from flask import Blueprint
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
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ClientMetadata
from flask_pyoidc.provider_configuration import ProviderConfiguration
from sqlalchemy import exc
from webdav3.client import Client as webdavClient
from webdav3.exceptions import WebDavException
from werkzeug.utils import secure_filename

from . import cache
from .session import get_authenticated_attendee_fullname
from .session import get_current_user
from .session import has_user_session
from .templates.content import FAQ_CONTENT
from .utils import is_accepted_email
from .utils import is_valid_email
from .utils import send_mail


bp = Blueprint("routes", __name__)


user_provider_configuration = ProviderConfiguration(
    issuer=current_app.config["OIDC_ISSUER"],
    userinfo_http_method=current_app.config["OIDC_USERINFO_HTTP_METHOD"],
    client_metadata=ClientMetadata(
        client_id=current_app.config["OIDC_CLIENT_ID"],
        client_secret=current_app.config["OIDC_CLIENT_SECRET"],
        token_endpoint_auth_method=current_app.config["OIDC_CLIENT_AUTH_METHOD"],
        post_logout_redirect_uris=[f'{current_app.config.get("SERVER_FQDN")}/logout'],
    ),
    auth_request_params={"scope": current_app.config["OIDC_SCOPES"]},
)
attendee_provider_configuration = ProviderConfiguration(
    issuer=current_app.config.get("OIDC_ATTENDEE_ISSUER"),
    userinfo_http_method=current_app.config.get("OIDC_ATTENDEE_USERINFO_HTTP_METHOD"),
    client_metadata=ClientMetadata(
        client_id=current_app.config.get("OIDC_ATTENDEE_CLIENT_ID"),
        client_secret=current_app.config.get("OIDC_ATTENDEE_CLIENT_SECRET"),
        token_endpoint_auth_method=current_app.config.get(
            "OIDC_ATTENDEE_CLIENT_AUTH_METHOD"
        ),
        post_logout_redirect_uris=[f'{current_app.config.get("SERVER_FQDN")}/logout'],
    ),
    auth_request_params={"scope": current_app.config["OIDC_ATTENDEE_SCOPES"]},
)

auth = OIDCAuthentication(
    {
        "default": user_provider_configuration,
        "attendee": attendee_provider_configuration,
    },
    current_app,
)


def meeting_mailto_params(meeting, role):
    if role == "moderator":
        return render_template(
            "meeting/mailto/mail_href.txt", meeting=meeting, role="moderator"
        ).replace("\n", "%0D%0A")
    elif role == "attendee":
        return render_template(
            "meeting/mailto/mail_href.txt", meeting=meeting, role="attendee"
        ).replace("\n", "%0D%0A")


@cache.cached(
    timeout=current_app.config["STATS_CACHE_DURATION"], key_prefix="meetings_stats"
)
def get_meetings_stats():
    # TODO: do this asynchroneously
    # Currently, the page needs to wait another network request in get_meetings_stats
    # before it can be rendered. This is mitigated by caching though.

    if not current_app.config["STATS_URL"]:
        return None

    response = requests.get(current_app.config["STATS_URL"])
    if response.status_code != 200:
        return None

    try:
        stats_array = response.content.decode(encoding="utf-8").split("\n")
        stats_array = [row.split(",") for row in stats_array]
        participant_count = int(stats_array[current_app.config["STATS_INDEX"]][1])
        running_count = int(stats_array[current_app.config["STATS_INDEX"]][2])
    except Exception:
        return None

    result = {"participantCount": participant_count, "runningCount": running_count}
    return result


@bp.route("/api/meetings")
@auth.token_auth(provider_name="default")
def api_meetings():
    if not auth.current_token_identity:
        return redirect(url_for("routes.index"))

    info = {
        "given_name": auth.current_token_identity["given_name"],
        "family_name": auth.current_token_identity["family_name"],
        "email": auth.current_token_identity["email"],
    }
    user = get_or_create_user(info)
    return {
        "meetings": [
            {
                "name": m.name,
                "moderator_url": m.get_signin_url("moderator"),
                "attendee_url": m.get_signin_url("attendee"),
            }
            for m in user.meetings
        ]
    }


# called by NextcloudfilePicker when documents should be added to a running room:
@bp.route("/meeting/files/<int:meeting_id>/insertDocuments", methods=["POST"])
@auth.oidc_auth("default")
def insertDocuments(meeting_id):
    from flask import request

    meeting = db.session.get(Meeting, meeting_id)
    files_title = request.get_json()
    secret_key = current_app.config["SECRET_KEY"]

    xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
    xml_end = " </module></modules>"
    xml_mid = ""
    # @FIX We ONLY send the documents that have been uploaded NOW, not ALL of them for this meetingid ;)
    for cur_file in files_title:
        id = add_external_meeting_file_nextcloud(cur_file, meeting_id)
        filehash = hashlib.sha1(
            f"{secret_key}-1-{id}-{secret_key}".encode()
        ).hexdigest()
        xml_mid += f"<document url='{current_app.config['SERVER_FQDN']}/ncdownload/1/{id}/{filehash}' filename='{cur_file}' />"

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


@bp.route("/mentions_legales")
def mentions_legales():
    return render_template(
        "footer/mentions_legales.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/cgu")
def cgu():
    return render_template(
        "footer/cgu.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/donnees_personnelles")
def donnees_personnelles():
    return render_template(
        "footer/donnees_personnelles.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/accessibilite")
def accessibilite():
    return render_template(
        "footer/accessibilite.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/documentation")
def documentation():
    if current_app.config["DOCUMENTATION_LINK"]["is_external"]:
        return redirect(current_app.config["DOCUMENTATION_LINK"]["url"])
    return render_template(
        "footer/documentation.html",
    )


@bp.route("/faq")
def faq():
    return render_template(
        "faq.html",
        contents=FAQ_CONTENT,
    )


@bp.route("/")
def index():
    if has_user_session():
        return redirect(url_for("routes.welcome"))
    else:
        return redirect(url_for("routes.home"))


@bp.route("/home")
def home():
    if has_user_session():
        return redirect(url_for("routes.welcome"))

    stats = get_meetings_stats()
    return render_template(
        "index.html",
        stats=stats,
        mail_meeting=current_app.config["MAIL_MEETING"],
        max_participants=current_app.config["MAX_PARTICIPANTS"],
    )


@bp.route("/welcome")
@auth.oidc_auth("default")
def welcome():
    user = get_current_user()
    stats = get_meetings_stats()

    return render_template(
        "welcome.html",
        stats=stats,
        max_participants=current_app.config["MAX_PARTICIPANTS"],
        can_create_meetings=user.can_create_meetings,
        max_meetings_per_user=current_app.config["MAX_MEETINGS_PER_USER"],
        meeting_mailto_params=meeting_mailto_params,
        mailto=current_app.config["MAILTO_LINKS"],
        quick_meeting=current_app.config["QUICK_MEETING"],
        file_sharing=current_app.config["FILE_SHARING"],
        clipboard=current_app.config["CLIPBOARD"],
    )


@bp.route("/meeting/mail", methods=["POST"])
def quick_mail_meeting():
    #### Almost the same as quick meeting but we do not redirect to join
    email = request.form.get("mail")
    if not is_valid_email(email):
        flash(
            _(
                "Courriel invalide. Avez vous bien tapé votre email ? Vous pouvez réessayer."
            ),
            "error_login",
        )
        return redirect(url_for("routes.index"))
    if not is_accepted_email(email):
        flash(
            _(
                "Ce courriel ne correspond pas à un service de l'État. Si vous appartenez à un service de l'État mais votre courriel n'est pas reconnu par Webinaire, contactez-nous pour que nous le rajoutions!"
            ),
            "error_login",
        )
        return redirect(url_for("routes.index"))
    user = User(
        id=email
    )  # this user can probably be removed if we created adock function
    meeting = get_quick_meeting_from_user_and_random_string(user)
    send_mail(meeting, email)
    flash(_("Vous avez reçu un courriel pour vous connecter"), "success_login")
    return redirect(url_for("routes.index"))


@bp.route("/meeting/quick")
@auth.oidc_auth("default")
def quick_meeting():
    user = get_current_user()
    fullname = user.fullname
    meeting = get_quick_meeting_from_user_and_random_string(user)
    return redirect(meeting.get_join_url("moderator", fullname, create=True))


@bp.route("/meeting/show/<int:meeting_id>")
@auth.oidc_auth("default")
def show_meeting(meeting_id):
    # TODO: appears unused

    form = ShowMeetingForm(data={"meeting_id": meeting_id})
    if not form.validate():
        flash(
            _("Vous ne pouvez pas voir cet élément (identifiant incorrect)"),
            "warning",
        )
        return redirect(url_for("routes.welcome"))
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)
    if meeting.user_id == user.id:
        return render_template(
            "meeting/show.html",
            meeting_mailto_params=meeting_mailto_params,
            meeting=meeting,
        )
    flash(_("Vous ne pouvez pas consulter cet élément"), "warning")
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/recordings/<int:meeting_id>")
@auth.oidc_auth("default")
def show_meeting_recording(meeting_id):
    form = ShowMeetingForm(data={"meeting_id": meeting_id})
    if not form.validate():
        flash(
            _("Vous ne pouvez pas voir cet élément (identifiant incorrect)"),
            "warning",
        )
        return redirect(url_for("routes.welcome"))
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)
    if meeting.user_id == user.id:
        form = RecordingForm()
        return render_template(
            "meeting/recordings.html",
            meeting_mailto_params=meeting_mailto_params,
            meeting=meeting,
            form=form,
        )
    flash(_("Vous ne pouvez pas consulter cet élément"), "warning")
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/<int:meeting_id>/recordings/<recording_id>", methods=["POST"])
@auth.oidc_auth("default")
def update_recording_name(meeting_id, recording_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id) or abort(404)
    if meeting.user_id == user.id:
        form = RecordingForm(request.form)
        form.validate() or abort(403)
        result = meeting.update_recording_name(recording_id, form.data["name"])
        return_code = result.get("returncode")
        if return_code == "SUCCESS":
            flash("Enregistrement renommé", "success")
        else:
            message = result.get("message", "")
            flash(
                "Nous n'avons pas pu modifier cet enregistrement : {code}, {message}".format(
                    code=return_code, message=message
                ),
                "error",
            )
    else:
        flash("Vous ne pouvez pas modifier cet enregistrement", "error")
    return redirect(url_for("routes.show_meeting_recording", meeting_id=meeting_id))


@bp.route("/meeting/new")
@auth.oidc_auth("default")
def new_meeting():
    user = get_current_user()
    if not user.can_create_meetings:
        return redirect(url_for("routes.welcome"))

    form = MeetingWithRecordForm() if current_app.config["RECORDING"] else MeetingForm()

    return render_template(
        "meeting/wizard.html",
        meeting=None,
        form=form,
        recording=current_app.config["RECORDING"],
    )


@bp.route("/meeting/edit/<int:meeting_id>")
@auth.oidc_auth("default")
def edit_meeting(meeting_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)

    form = (
        MeetingWithRecordForm(obj=meeting)
        if current_app.config["RECORDING"]
        else MeetingForm(obj=meeting)
    )
    if meeting and meeting.user_id == user.id:
        return render_template(
            "meeting/wizard.html",
            meeting=meeting,
            form=form,
            recording=current_app.config["RECORDING"],
        )
    flash("Vous ne pouvez pas modifier cet élément", "warning")
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/files/<int:meeting_id>")
@auth.oidc_auth("default")
def edit_meeting_files(meeting_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)

    form = MeetingFilesForm()

    if current_app.config["FILE_SHARING"]:
        # we test webdav connection here, with a simple 'list' command
        if user.nc_login and user.nc_token and user.nc_locator:
            options = {
                "webdav_root": f"/remote.php/dav/files/{user.nc_login}/",
                "webdav_hostname": user.nc_locator,
                "webdav_verbose": True,
                "webdav_token": user.nc_token,
            }
            try:
                client = webdavClient(options)
                client.list()
            except WebDavException as exception:
                current_app.logger.warning(
                    "WebDAV error, user data disabled: %s", exception
                )
                user.disable_nextcloud()

        if user is not None and meeting.user_id == user.id:
            return render_template(
                "meeting/filesform.html",
                meeting=meeting,
                form=form,
            )
    flash(_("Vous ne pouvez pas modifier cet élément"), "warning")
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/files/<int:meeting_id>/<int:file_id>")
@auth.oidc_auth("default")
def download_meeting_files(meeting_id, file_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)

    TMP_DOWNLOAD_DIR = current_app.config["TMP_DOWNLOAD_DIR"]
    Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    tmpName = f'{current_app.config["TMP_DOWNLOAD_DIR"]}{secrets.token_urlsafe(32)}'
    fileToSend = None
    if user is not None and meeting.user_id == user.id:
        for curFile in meeting.files:
            if curFile.id == file_id:
                fileToSend = curFile
                break
        if not fileToSend:
            return jsonify(status=404, msg="file not found")
        if curFile.url:
            response = requests.get(curFile.url)
            open(tmpName, "wb").write(response.content)
            return send_file(tmpName, as_attachment=True, download_name=curFile.title)
        else:
            # get file from nextcloud WEBDAV and send it
            try:
                davUser = {
                    "nc_locator": user.nc_locator,
                    "nc_login": user.nc_login,
                    "nc_token": user.nc_token,
                }
                options = {
                    "webdav_root": f"/remote.php/dav/files/{davUser['nc_login']}/",
                    "webdav_hostname": davUser["nc_locator"],
                    "webdav_verbose": True,
                    "webdav_token": davUser["nc_token"],
                }
                client = webdavClient(options)
                kwargs = {
                    "remote_path": curFile.nc_path,
                    "local_path": f"{tmpName}",
                }
                client.download_sync(**kwargs)
                return send_file(
                    tmpName, as_attachment=True, download_name=curFile.title
                )
            except WebDavException as exception:
                user.disable_nextcloud()
                current_app.logger.warning(
                    "webdav call encountered following exception : %s", exception
                )
                flash("Le fichier ne semble pas accessible", "error")
                return redirect(url_for("routes.welcome"))
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/files/<int:meeting_id>/toggledownload", methods=["POST"])
@auth.oidc_auth("default")
def toggledownload(meeting_id):
    user = get_current_user()
    data = request.get_json()

    if user is None:
        return redirect(url_for("routes.welcome"))
    meeting = db.session.get(Meeting, meeting_id)
    meeting_file = db.session.get(MeetingFiles, data["id"])
    if meeting_file is not None and meeting.user_id == user.id:
        meeting_file.is_downloadable = data["value"]
        meeting_file.save()

        return jsonify(status=200, id=data["id"])
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/files/<int:meeting_id>/default", methods=["POST"])
@auth.oidc_auth("default")
def set_meeting_default_file(meeting_id):
    user = get_current_user()
    data = request.get_json()

    meeting = db.session.get(Meeting, meeting_id)
    if meeting.user_id == user.id:
        actual_default_file = meeting.default_file
        if actual_default_file:
            actual_default_file.is_default = False

        meeting_file = MeetingFiles()
        meeting_file = meeting_file.query.get(data["id"])
        meeting_file.is_default = True

        if actual_default_file:
            actual_default_file.save()
        meeting_file.save()

    return jsonify(status=200, id=data["id"])


def removeDropzoneFile(absolutePath):
    os.remove(absolutePath)


# called when a file has been uploaded : send it to nextcloud
def add_meeting_file_dropzone(title, meeting_id, is_default):
    user = get_current_user()
    # should be in /tmp/visioagent/dropzone/USER_ID-TITLE
    DROPZONE_DIR = os.path.join(current_app.config["UPLOAD_DIR"], "dropzone")
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    dropzone_path = os.path.join(DROPZONE_DIR, f"{user.id}-{meeting_id}-{title}")
    metadata = os.stat(dropzone_path)
    if int(metadata.st_size) > int(current_app.config["MAX_SIZE_UPLOAD"]):
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

        meeting_file = MeetingFiles()
        meeting_file.nc_path = nc_path

        meeting_file.title = title
        meeting_file.created_at = date.today()
        meeting_file.meeting_id = meeting_id
    except WebDavException as exception:
        user.disable_nextcloud()
        current_app.logger.warning("WebDAV error: %s", exception)
        return jsonify(
            status=500, isfrom="dropzone", msg="La connexion avec Nextcloud est rompue"
        )

    try:
        # test for is_default-file absence at the latest time possible
        meeting = db.session.get(Meeting, meeting_id)
        if len(meeting.files) == 0 and not meeting.default_file:
            meeting_file.is_default = True
        else:
            meeting_file.is_default = False

        meeting_file.save()
        current_app.config["SECRET_KEY"]
        meeting_file.update()
        # file has been associated AND uploaded to nextcloud, we can safely remove it from visio-agent tmp directory
        removeDropzoneFile(dropzone_path)
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
        return jsonify(status=500, isfrom="dropzone", msg="File already exists")


def add_meeting_file_URL(url, meeting_id, is_default):
    title = url.rsplit("/", 1)[-1]

    # test MAX_SIZE_UPLOAD for 20Mo
    metadata = requests.head(url)
    if not metadata.ok:
        return jsonify(
            status=404,
            isfrom="url",
            msg=f"Fichier {title} NON DISPONIBLE, veuillez vérifier l'URL proposée",
        )

    if int(metadata.headers["content-length"]) > int(
        current_app.config["MAX_SIZE_UPLOAD"]
    ):
        return jsonify(
            status=500,
            isfrom="url",
            msg=f"Fichier {title} TROP VOLUMINEUX, ne pas dépasser 20Mo",
        )

    meeting_file = MeetingFiles()

    meeting_file.title = title
    meeting_file.created_at = date.today()
    meeting_file.meeting_id = meeting_id
    meeting_file.url = url
    meeting_file.is_default = is_default

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
        return jsonify(status=500, isfrom="url", msg="File already exists")


def add_meeting_file_nextcloud(path, meeting_id, is_default):
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
    if int(metadata["size"]) > int(current_app.config["MAX_SIZE_UPLOAD"]):
        return jsonify(
            status=500,
            isfrom="nextcloud",
            msg=f"Fichier {path} TROP VOLUMINEUX, ne pas dépasser 20Mo",
        )

    meeting_file = MeetingFiles()

    meeting_file.title = path
    meeting_file.created_at = date.today()
    meeting_file.meeting_id = meeting_id
    meeting_file.nc_path = path
    meeting_file.is_default = is_default
    current_app.config["SECRET_KEY"]

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
        return jsonify(status=500, isfrom="nextcloud", msg="File already exists")


def add_external_meeting_file_nextcloud(path, meeting_id):
    externalMeetingFile = MeetingFilesExternal()

    externalMeetingFile.title = path
    externalMeetingFile.meeting_id = meeting_id
    externalMeetingFile.nc_path = path

    externalMeetingFile.save()
    return externalMeetingFile.id


@bp.route("/meeting/files/<int:meeting_id>", methods=["POST"])
@auth.oidc_auth("default")
def add_meeting_files(meeting_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)

    data = request.get_json()
    is_default = False
    if len(meeting.files) == 0:
        is_default = True
    if meeting.user_id == user.id:
        if data["from"] == "nextcloud":
            return add_meeting_file_nextcloud(data["value"], meeting_id, is_default)
        if data["from"] == "URL":
            return add_meeting_file_URL(data["value"], meeting_id, is_default)
        if data["from"] == "dropzone":
            return add_meeting_file_dropzone(
                secure_filename(data["value"]), meeting_id, is_default
            )
        else:
            return make_response(jsonify("no file provided"), 200)

    return jsonify(status=500, msg="Vous ne pouvez pas modifier cet élément")


# for dropzone multiple files uploading at once
@bp.route("/meeting/files/<int:meeting_id>/dropzone", methods=["POST"])
@auth.oidc_auth("default")
def add_dropzone_files(meeting_id):
    user = get_current_user()

    meeting = db.session.get(Meeting, meeting_id)
    if meeting and user and meeting.user_id == user.id:
        return upload(user, meeting_id, request.files["dropzoneFiles"])
    else:
        flash("Traitement de requête impossible", "error")
        return redirect(url_for("routes.welcome"))


# for dropzone chunk file by file validation
# shamelessly taken from https://stackoverflow.com/questions/44727052/handling-large-file-uploads-with-flask
def upload(user, meeting_id, file):
    DROPZONE_DIR = os.path.join(current_app.config["UPLOAD_DIR"], "dropzone")
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join(
        DROPZONE_DIR, secure_filename(f"{user.id}-{meeting_id}-{file.filename}")
    )
    current_chunk = int(request.form["dzchunkindex"])

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(("File already exists", 500))

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

    return make_response(("Chunk upload successful", 200))


@bp.route("/meeting/files/delete", methods=["POST"])
@auth.oidc_auth("default")
def delete_meeting_file():
    user = get_current_user()
    data = request.get_json()
    meeting_file_id = data["id"]
    meeting_file = MeetingFiles()
    meeting_file = meeting_file.query.get(meeting_file_id)
    meeting = Meeting()
    cur_meeting = meeting.query.get(meeting_file.meeting_id)

    if cur_meeting.user_id == user.id:
        db.session.delete(meeting_file)
        db.session.commit()
        new_default_id = None
        if meeting_file.is_default:
            cur_meeting = meeting.query.get(meeting_file.meeting_id)
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
    return jsonify(
        status=500, id=data["id"], msg="Vous ne pouvez pas supprimer cet élément"
    )


@bp.route("/meeting/save", methods=["POST"])
@auth.oidc_auth("default")
def save_meeting():
    user = get_current_user()
    form = (
        MeetingWithRecordForm(request.form)
        if current_app.config["RECORDING"]
        else MeetingForm(request.form)
    )

    is_new_meeting = not form.data["id"]
    if not user.can_create_meetings and is_new_meeting:
        return redirect(url_for("routes.welcome"))

    if not form.validate():
        flash("Le formulaire contient des erreurs", "error")
        return render_template(
            "meeting/wizard.html",
            meeting=None if is_new_meeting else db.session.get(Meeting, form.id.data),
            form=form,
            recording=current_app.config["RECORDING"],
        )

    if is_new_meeting:
        meeting = Meeting()
        meeting.user = user
    else:
        meeting_id = form.data["id"]
        meeting = db.session.get(Meeting, meeting_id)
        del form.id
        del form.name

    meeting.record = bool(
        form.data.get("allowStartStopRecording") or form.data.get("autoStartRecording")
    )
    form.populate_obj(meeting)
    meeting.save()
    flash(
        _("%(meeting_name)s modifications prises en compte", meeting_name=meeting.name),
        "success",
    )

    if meeting.is_running():
        return render_template(
            "meeting/end.html",
            meeting=meeting,
            form=EndMeetingForm(data={"meeting_id": meeting_id}),
        )
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/end", methods=["POST"])
@auth.oidc_auth("default")
def end_meeting():
    user = get_current_user()
    form = EndMeetingForm(request.form)

    meeting_id = form.data["meeting_id"]
    meeting = db.session.get(Meeting, meeting_id) or abort(404)

    if user == meeting.user:
        meeting.end_bbb()
        flash(
            f"{current_app.config['WORDING_MEETING'].capitalize()} « {meeting.name} » terminé(e)",
            "success",
        )
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/create/<int:meeting_id>")
@auth.oidc_auth("default")
def create_meeting(meeting_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)
    if meeting.user_id == user.id:
        meeting.create_bbb()
        meeting.save()
    return redirect(url_for("routes.welcome"))


# draft for insertDocument calls to BBB API
# @TODO: can we remove this def entirely?
@bp.route("/insertDoc/<token>")
def insertDoc(token):
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
    xml = f"<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'><document url='{current_app.config['SERVER_FQDN']}/ncdownload/{meeting_file.id}/{meeting_file.download_hash}' filename='{meeting_file.title}' /> </module></modules>"

    requests.post(
        f"{current_app.config['BIGBLUEBUTTON_ENDPOINT']}/insertDocument",
        data=xml,
        headers=headers,
        params=params,
    )

    return make_response("ok", 200)


@bp.route("/meeting/<int:meeting_id>/externalUpload")
@auth.oidc_auth("default")
def externalUpload(meeting_id):
    user = get_current_user()
    meeting = db.session.get(Meeting, meeting_id)
    if (
        meeting is not None
        and meeting.is_running()
        and user is not None
        and meeting.user_id == user.id
    ):
        return render_template("meeting/externalUpload.html", meeting=meeting)
    else:
        return redirect(url_for("routes.welcome"))


@bp.route("/ncdownload/<isexternal>/<mfid>/<mftoken>")
# @auth.token_auth(provider_name="default") - must be accessible by BBB server, so no auth
def ncdownload(isexternal, mfid, mftoken):
    secret_key = current_app.config["SECRET_KEY"]
    # select good file from token
    # get file through NC credentials - HOW POSSIBLE ?
    # return file as response to BBB server
    # isexternal tells if the file has been chosen earlier from the visio-agent interface (0) or if it has been uploaded from BBB itself (1)
    if str(isexternal) == "0":
        isexternal = "0"
        meeting_file = MeetingFiles.query.filter_by(id=mfid).one_or_none()
    else:
        isexternal = "1"
        meeting_file = MeetingFilesExternal.query.filter_by(id=mfid).one_or_none()

    if not meeting_file:
        return make_response("Bad token provided, no file matching", 404)

    # the hash token consist of the sha1 of "secret key - 0/1 (internal/external) - id in the DB - secret key"
    if (
        mftoken
        != hashlib.sha1(
            f"{secret_key}-{isexternal}-{mfid}-{secret_key}".encode()
        ).hexdigest()
    ):
        return make_response("Bad token provided, no file matching", 404)

    # download the file using webdavClient from the Nextcloud to a temporary folder (that will need cleaning)
    options = {
        "webdav_root": f"/remote.php/dav/files/{meeting_file.meeting.user.nc_login}/",
        "webdav_hostname": meeting_file.meeting.user.nc_locator,
        "webdav_verbose": True,
        "webdav_token": meeting_file.meeting.user.nc_token,
    }
    try:
        client = webdavClient(options)
        TMP_DOWNLOAD_DIR = current_app.config["TMP_DOWNLOAD_DIR"]
        Path(TMP_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        uniqfile = str(uuid.uuid4())
        tmpName = f"{TMP_DOWNLOAD_DIR}{uniqfile}"
        kwargs = {
            "remote_path": meeting_file.nc_path,
            "local_path": tmpName,
        }
        client.download_sync(**kwargs)
    except WebDavException:
        meeting_file.meeting.user.disable_nextcloud()
        return jsonify(status=500, msg="La connexion avec Nextcloud semble rompue")
    # send the downloaded file to the BBB:
    return send_from_directory(TMP_DOWNLOAD_DIR, uniqfile)


@bp.route(
    "/meeting/signinmail/<meeting_fake_id>/expiration/<expiration>/hash/<h>",
)
def signin_mail_meeting(meeting_fake_id, expiration, h):
    meeting = get_mail_meeting(meeting_fake_id)
    wordings = current_app.config["WORDINGS"]

    if meeting is None:
        flash(
            _(
                "Aucune %(meeting_label)s ne correspond à ces paramètres",
                meeting_label=wordings["meeting_label"],
            ),
            "success",
        )
        return redirect(url_for("routes.index"))

    hash_matches = meeting.get_mail_signin_hash(meeting_fake_id, expiration) == h
    if not hash_matches:
        flash(_("Lien invalide"), "error")
        return redirect(url_for("routes.index"))

    is_expired = datetime.fromtimestamp(float(expiration)) < datetime.now()
    if is_expired:
        flash(_("Lien expiré"), "error")
        return redirect(url_for("routes.index"))

    return render_template(
        "meeting/joinmail.html",
        meeting=meeting,
        meeting_fake_id=meeting.fake_id,
        expiration=expiration,
        user_id="fakeuserId",
        h=h,
        role="moderator",
    )


@bp.route("/meeting/signin/<meeting_fake_id>/creator/<int:user_id>/hash/<h>")
def signin_meeting(meeting_fake_id, user_id, h):
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    wordings = current_app.config["WORDINGS"]
    if meeting is None:
        flash(
            _(
                "Aucune %(meeting_label)s ne correspond à ces paramètres",
                meeting_label=wordings["meeting_label"],
            ),
            "success",
        )
        return redirect(url_for("routes.index"))

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)

    if role == "authenticated":
        return redirect(
            url_for("routes.join_meeting_as_authenticated", meeting_id=meeting_fake_id)
        )
    elif not role:
        return redirect(url_for("routes.index"))

    return render_template(
        "meeting/join.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        user_id=user_id,
        h=h,
        role=role,
    )


@bp.route("/meeting/auth/<meeting_fake_id>/creator/<int:user_id>/hash/<h>")
@auth.oidc_auth("default")
def authenticate_then_signin_meeting(meeting_fake_id, user_id, h):
    return redirect(
        url_for(
            "routes.signin_meeting",
            meeting_fake_id=meeting_fake_id,
            user_id=user_id,
            h=h,
        )
    )


@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user_id>/hash/<h>/fullname/fullname_suffix/",
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user_id>/hash/<h>/fullname/<path:fullname>/fullname_suffix/",
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user_id>/hash/<h>/fullname/fullname_suffix/<path:fullname_suffix>",
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user_id>/hash/<h>/fullname/<path:fullname>/fullname_suffix/<path:fullname_suffix>",
)
def waiting_meeting(meeting_fake_id, user_id, h, fullname="", fullname_suffix=""):
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    if meeting is None:
        return redirect(url_for("routes.index"))

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)
    if not role:
        return redirect(url_for("routes.index"))

    return render_template(
        "meeting/wait.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        user_id=user_id,
        h=h,
        role=role,
        fullname=fullname,
        fullname_suffix=fullname_suffix,
    )


@bp.route("/meeting/join", methods=["POST"])
def join_meeting():
    form = JoinMeetingForm(request.form)
    if not form.validate():
        return redirect(url_for("routes.index"))

    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    user_id = form["user_id"].data
    h = form["h"].data
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    if meeting is None:
        return redirect(url_for("routes.index"))

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)
    fullname_suffix = form["fullname_suffix"].data
    if role == "authenticated":
        fullname = get_authenticated_attendee_fullname()
    elif not role:
        return redirect(url_for("routes.index"))

    return redirect(
        meeting.get_join_url(
            role, fullname, fullname_suffix=fullname_suffix, create=True
        )
    )


@bp.route("/meeting/joinmail", methods=["POST"])
def join_mail_meeting():
    form = JoinMailMeetingForm(request.form)
    if not form.validate():
        flash("Lien invalide", "error")
        return redirect(url_for("routes.index"))

    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    form["user_id"].data
    expiration = form["expiration"].data
    h = form["h"].data

    meeting = get_mail_meeting(meeting_fake_id)
    if meeting is None:
        flash(
            _(
                "%(meeting_label)s inexistante",
                meeting_label=current_app.config["WORDINGS"][
                    "meeting_label"
                ].capitalize(),
            ),
            "error",
        )
        return redirect(url_for("routes.index"))

    hash_matches = meeting.get_mail_signin_hash(meeting_fake_id, expiration) == h
    if not hash_matches:
        flash(_("Lien invalide"), "error")
        return redirect(url_for("routes.index"))

    is_expired = datetime.fromtimestamp(expiration) < datetime.now()
    if is_expired:
        flash(_("Lien expiré"), "error")
        return redirect(url_for("routes.index"))

    return redirect(meeting.get_join_url("moderator", fullname, create=True))


@bp.route("/meeting/join/<int:meeting_id>/authenticated")
@auth.oidc_auth("attendee")
def join_meeting_as_authenticated(meeting_id):
    meeting = db.session.get(Meeting, meeting_id) or abort(404)
    role = "authenticated"
    fullname = get_authenticated_attendee_fullname()
    return redirect(
        url_for(
            "routes.waiting_meeting",
            meeting_fake_id=meeting_id,
            user_id=meeting.user.id,
            h=meeting.get_hash(role),
            fullname=fullname,
        )
    )


@bp.route("/meeting/join/<int:meeting_id>/<role>")
@auth.oidc_auth("default")
def join_meeting_as_role(meeting_id, role):
    user = get_current_user()
    form = JoinMeetingAsRoleForm(data={"meeting_id": meeting_id, "role": role})
    if not form.validate():
        abort(404)

    meeting = db.session.get(Meeting, meeting_id) or abort(404)
    if meeting.user_id == user.id:
        return redirect(meeting.get_join_url(role, user.fullname, create=True))
    else:
        flash(_("Accès non autorisé"), "error")
        return redirect(url_for("routes.index"))


@bp.route("/meeting/delete", methods=["POST", "GET"])
@auth.oidc_auth("default")
def delete_meeting():
    if request.method == "POST":
        user = get_current_user()
        meeting_id = request.form["id"]
        meeting = db.session.get(Meeting, meeting_id)

        if meeting.user_id == user.id:
            for meeting_file in meeting.files:
                db.session.delete(meeting_file)
            for meeting_file_external in meeting.externalFiles:
                db.session.delete(meeting_file_external)

            data = meeting.delete_all_recordings()
            return_code = data.get("returncode", "SUCCESS")
            if return_code != "SUCCESS":
                message = data.get("message", "")
                flash(
                    "Nous n'avons pas pu supprimer les vidéos de cette "
                    + current_app.config["WORDINGS"]["meeting_label"]
                    + f" : {message}",
                    "error",
                )
            else:
                db.session.delete(meeting)
                db.session.commit()
                flash(_("Élément supprimé"), "success")
        else:
            flash(_("Vous ne pouvez pas supprimer cet élément"), "error")
    return redirect(url_for("routes.welcome"))


@bp.route("/meeting/video/delete", methods=["POST"])
@auth.oidc_auth("default")
def delete_video_meeting():
    user = get_current_user()
    meeting_id = request.form["id"]
    meeting = db.session.get(Meeting, meeting_id)
    if meeting.user_id == user.id:
        recordID = request.form["recordID"]
        data = meeting.delete_recordings(recordID)
        return_code = data.get("returncode")
        if return_code == "SUCCESS":
            flash(_("Vidéo supprimée"), "success")
        else:
            message = data.get("message", "")
            flash(
                _(
                    "Nous n'avons pas pu supprimer cette vidéo : %(code)s, %(message)s",
                    code=return_code,
                    message=message,
                ),
                "error",
            )
    else:
        flash(
            _("Vous ne pouvez pas supprimer cette enregistrement"),
            "error",
        )
    return redirect(url_for("routes.welcome"))


@bp.route("/logout")
@auth.oidc_logout
def logout():
    return redirect(url_for("routes.index"))
