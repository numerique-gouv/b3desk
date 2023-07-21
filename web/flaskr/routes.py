# -*- coding: utf-8 -*-
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

from werkzeug.utils import secure_filename

from webdav3.client import Client as webdavClient
from webdav3.exceptions import MethodNotSupported, WebDavException

from pathlib import Path

import filetype

from flask import (
    current_app,
    send_from_directory,
    abort,
    Blueprint,
    render_template,
    send_file,
    make_response,
    Response,
    request,
    redirect,
    flash,
    session,
    jsonify,
    url_for,
)
from xml.etree import ElementTree
from flask_babel import lazy_gettext
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import (
    ProviderConfiguration,
    ClientMetadata,
)
from flask_pyoidc.user_session import UserSession
from sqlalchemy import or_, exc
import random
import hashlib
import os
import re
import smtplib
import string
import requests
import shutil
import secrets
import uuid

from datetime import datetime, date
from email.mime.text import MIMEText
from email.message import EmailMessage
from urllib.parse import quote
from netaddr import IPNetwork, IPAddress

from flaskr.forms import (
    JoinMeetingAsRoleForm,
    JoinMeetingForm,
    JoinMailMeetingForm,
    ShowMeetingForm,
    MeetingForm,
    MeetingFilesForm,
    MeetingWithRecordForm,
    EndMeetingForm,
    RecordingForm,
)
from flaskr.models import (
    get_or_create_user,
    db,
    User,
    Meeting,
    MeetingFiles,
    MeetingFilesExternal,
)
from flaskr.utils import retry_join_meeting
from .common.extensions import cache
from .templates.content import FAQ_CONTENT


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
    auth_request_params={
        "scope": current_app.config.get("OIDC_ATTENDEE_SCOPES")
        or current_app.config["OIDC_SCOPES"]
    },
)

auth = OIDCAuthentication(
    {
        "default": user_provider_configuration,
        "attendee": attendee_provider_configuration,
    },
    current_app,
)


def is_accepted_email(email):
    for regex in current_app.config["EMAIL_WHITELIST"]:
        if re.search(regex, email):
            return True
    return False


def is_valid_email(email):
    if not email or not re.search(
        r"^([a-zA-Z0-9_\-\.']+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$", email
    ):
        return False
    return True


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = "".join((random.choice(letters_and_digits) for i in range(length)))
    return result_str


def get_quick_meeting_from_fake_id(fake_id):
    try:
        user_id_str, random_string = fake_id.split("-")
        user = User.query.get(int(user_id_str))
        return get_quick_meeting_from_user_and_random_string(user, random_string)
    except:
        return None


def get_quick_meeting_from_user_and_random_string(user, random_string=None):
    if random_string is None:
        random_string = get_random_alphanumeric_string(8)
    m = Meeting()
    m.duration = current_app.config["DEFAULT_MEETING_DURATION"]
    m.user = user
    m.name = current_app.config["QUICK_MEETING_DEFAULT_NAME"]
    m.fake_id = random_string
    m.moderatorPW = "%s-%s" % (user.hash, random_string)
    m.attendeePW = "%s-%s" % (random_string, random_string)
    m.moderatorOnlyMessage = current_app.config[
        "QUICK_MEETING_MODERATOR_WELCOME_MESSAGE"
    ]
    m.logoutUrl = (
        current_app.config["QUICK_MEETING_LOGOUT_URL"]
        or current_app.config["SERVER_FQDN"]
    )
    return m


def get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id):
    if meeting_fake_id.isdigit():
        try:
            meeting = Meeting.query.get(meeting_fake_id)
        except:
            try:
                user = User.query.get(user_id)
                meeting = get_quick_meeting_from_user_and_random_string(
                    user, random_string=meeting_fake_id
                )
            except:
                meeting = None
    else:
        try:
            user = User.query.get(user_id)
            meeting = get_quick_meeting_from_user_and_random_string(
                user, random_string=meeting_fake_id
            )
        except:
            meeting = None

    return meeting


def get_fake_user():
    return User(email=current_app.config["SMTP_FROM"])


def get_current_user():
    user_session = UserSession(session)
    info = user_session.userinfo
    return get_or_create_user(info)


def has_user_session():
    user_session = UserSession(dict(session), "default")
    return user_session.is_authenticated()


@bp.context_processor
def global_processor():
    if has_user_session():
        user = get_current_user()
        return {
            "user": user,
            "fullname": user.fullname,
        }
    else:
        return {
            "user": None,
            "fullname": "",
        }


def add_mailto_links(meeting_data):
    d = meeting_data
    d["moderator_mailto_href"] = render_template(
        "meeting/mailto/mail_href.txt", meeting=meeting_data, role="moderator"
    ).replace("\n", "%0D%0A")
    d["attendee_mailto_href"] = render_template(
        "meeting/mailto/mail_href.txt", meeting=meeting_data, role="attendee"
    ).replace("\n", "%0D%0A")
    return d


@cache.cached(
    timeout=current_app.config["STATS_CACHE_DURATION"], key_prefix="meetings_stats"
)
def get_meetings_stats():
    response = requests.get(current_app.config["STATS_URL"])
    if response.status_code != 200:
        return None
    try:
        stats_array = response.content.decode(encoding="utf-8").split("\n")
        stats_array = [row.split(",") for row in stats_array]
        participantCount = int(stats_array[current_app.config["STATS_INDEX"]][1])
        runningCount = int(stats_array[current_app.config["STATS_INDEX"]][2])
    except Exception as e:
        return None

    result = {"participantCount": participantCount, "runningCount": runningCount}
    return result


@bp.route("/api/meetings", methods=["GET"])
@auth.token_auth(provider_name="default")
def api_meetings():
    if auth.current_token_identity:
        current_identity = auth.current_token_identity
    else:
        return redirect("/")
    info = {
        "given_name": auth.current_token_identity["given_name"],
        "family_name": auth.current_token_identity["family_name"],
        "email": auth.current_token_identity["email"],
    }
    user = get_or_create_user(info)
    fullname = user.fullname
    stats = get_meetings_stats()
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

    user = get_current_user()
    meeting = Meeting.query.get(meeting_id)
    files_title = request.get_json()
    secret_key = current_app.config["SECRET_KEY"]

    xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
    xml_end = " </module></modules>"
    xml_mid = ""
    # @FIX We ONLY send the documents that have been uploaded NOW, not ALL of them for this meetingid ;)
    for cur_file in files_title:
        id = add_external_meeting_file_nextcloud(cur_file, meeting_id)
        filehash = hashlib.sha1(
            f"{secret_key}-1-{id}-{secret_key}".encode("utf-8")
        ).hexdigest()
        xml_mid += f"<document url='{current_app.config['SERVER_FQDN']}/ncdownload/1/{id}/{filehash}' filename='{cur_file}' />"

    bbb_endpoint = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
    xml = xml_beg + xml_mid + xml_end
    params = {"meetingID": meeting.meetingID}
    request = requests.Request(
        "POST",
        "%s/%s" % (current_app.config["BIGBLUEBUTTON_ENDPOINT"], "insertDocument"),
        params=params,
    )
    headers = {"Content-Type": "application/xml"}
    pr = request.prepare()
    bigbluebutton_secret = current_app.config["BIGBLUEBUTTON_SECRET"]
    s = "%s%s" % (
        pr.url.replace("?", "").replace(
            current_app.config["BIGBLUEBUTTON_ENDPOINT"] + "/", ""
        ),
        bigbluebutton_secret,
    )
    params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()
    r = requests.post(
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
        return redirect("/welcome")
    else:
        return redirect("/home")


@bp.route("/home")
def home():
    is_rie = any(
        [
            IPAddress(request.remote_addr) in IPNetwork(network_ip)
            for network_ip in current_app.config["RIE_NETWORK_IPS"]
        ]
    )
    stats = get_meetings_stats()
    return render_template(
        "index.html",
        is_rie=is_rie,
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
        title=current_app.config["TITLE"],
        stats=stats,
        max_participants=current_app.config["MAX_PARTICIPANTS"],
        meetings=[
            add_mailto_links(m.get_data_as_dict(user.fullname)) for m in user.meetings
        ],
        can_create_meetings=user.can_create_meetings,
        max_meetings_per_user=current_app.config["MAX_MEETINGS_PER_USER"],
        mailto=current_app.config["MAILTO_LINKS"],
        quick_meeting=current_app.config["QUICK_MEETING"],
        shorty=current_app.config["SHORTY"],
        file_sharing=current_app.config["FILE_SHARING"],
        clipboard=current_app.config["CLIPBOARD"],
        recording=current_app.config["RECORDING"],
    )


def get_mail_meeting(random_string=None):
    # only used for mail meeting
    if random_string is None:
        random_string = get_random_alphanumeric_string(8)
    m = Meeting()
    m.duration = current_app.config["DEFAULT_MEETING_DURATION"]
    m.name = current_app.config["QUICK_MEETING_DEFAULT_NAME"]
    m.moderatorPW = "%s-%s" % (
        random_string,
        random_string,
    )  # it is only usefull for bbb
    m.fake_id = random_string
    m.moderatorOnlyMessage = current_app.config["MAIL_MODERATOR_WELCOME_MESSAGE"]
    m.logoutUrl = (
        current_app.config["QUICK_MEETING_LOGOUT_URL"]
        or current_app.config["SERVER_FQDN"]
    )
    return m


@bp.route("/meeting/mail", methods=["POST"])
def quick_mail_meeting():
    #### Almost the same as quick meeting but we do not redirect to join
    email = request.form.get("mail")
    if not is_valid_email(email):
        flash(
            lazy_gettext(
                "Courriel invalide. Avez vous bien tapé votre email ? Vous pouvez réessayer."
            ),
            "error_login",
        )
        return redirect("/")
    if not is_accepted_email(email):
        flash(
            lazy_gettext(
                "Ce courriel ne correspond pas à un service de l'État. Si vous appartenez à un service de l'État mais votre courriel n'est pas reconnu par Webinaire, contactez-nous pour que nous le rajoutions!"
            ),
            "error_login",
        )
        return redirect("/")
    user = User(
        id=email
    )  # this user can probably be removed if we created adock function
    m = get_quick_meeting_from_user_and_random_string(user)
    signinurl = _send_mail(m, email)
    flash(
        lazy_gettext("Vous avez reçu un courriel pour vous connecter"), "success_login"
    )
    return redirect("/")


def _send_mail(meeting, to_email):
    smtp_from = current_app.config["SMTP_FROM"]
    smtp_host = current_app.config["SMTP_HOST"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_ssl = current_app.config["SMTP_SSL"]
    smtp_username = current_app.config["SMTP_USERNAME"]
    smtp_password = current_app.config["SMTP_PASSWORD"]
    wordings = current_app.config["WORDINGS"]
    msg = EmailMessage()
    content = render_template(
        "meeting/mailto/mail_quick_meeting_body.txt",
        role="moderator",
        moderator_mail_signin_url=meeting.get_mail_signin_url(),
        welcome_url=current_app.config["SERVER_FQDN"] + "/welcome",
        meeting=meeting,
    )
    msg["Subject"] = wordings["meeting_mail_subject"]
    msg["From"] = smtp_from
    msg["To"] = to_email
    html = MIMEText(content, "html")
    msg.make_mixed()  # This converts the message to multipart/mixed
    msg.attach(html)

    if smtp_ssl:
        s = smtplib.SMTP_SSL(smtp_host, smtp_port)
    else:
        s = smtplib.SMTP(smtp_host, smtp_port)
    if smtp_username:
        # in dev, no need for username
        s.login(smtp_username, smtp_password)
    s.send_message(msg)
    s.quit()


@bp.route("/meeting/quick", methods=["GET"])
@auth.oidc_auth("default")
def quick_meeting():
    user = get_current_user()
    fullname = user.fullname
    m = get_quick_meeting_from_user_and_random_string(user)
    return redirect(m.get_join_url("moderator", fullname, create=True))


@bp.route("/meeting/show/<int:meeting_id>", methods=["GET"])
@auth.oidc_auth("default")
def show_meeting(meeting_id):
    form = ShowMeetingForm(data={"meeting_id": meeting_id})
    if not form.validate():
        flash(
            lazy_gettext("Vous ne pouvez pas voir cet élément (identifiant incorrect)"),
            "warning",
        )
        return redirect("/welcome")
    user = get_current_user()
    meeting = Meeting.query.get(meeting_id)
    if meeting.user_id == user.id:
        return render_template(
            "meeting/show.html",
            meeting=add_mailto_links(meeting.get_data_as_dict(user.fullname)),
        )
    flash(lazy_gettext("Vous ne pouvez pas consulter cet élément"), "warning")
    return redirect("/welcome")


@bp.route("/meeting/recordings/<int:meeting_id>", methods=["GET"])
@auth.oidc_auth("default")
def show_meeting_recording(meeting_id):
    form = ShowMeetingForm(data={"meeting_id": meeting_id})
    if not form.validate():
        flash(
            lazy_gettext("Vous ne pouvez pas voir cet élément (identifiant incorrect)"),
            "warning",
        )
        return redirect("/welcome")
    user = get_current_user()
    meeting = Meeting.query.get(meeting_id)
    if meeting.user_id == user.id:
        meeting_dict = meeting.get_data_as_dict(user.fullname, fetch_recording=True)
        form = RecordingForm()
        return render_template(
            "meeting/recordings.html",
            meeting=add_mailto_links(meeting_dict),
            form=form,
        )
    flash(lazy_gettext("Vous ne pouvez pas consulter cet élément"), "warning")
    return redirect("/welcome")


@bp.route("/meeting/<int:meeting_id>/recordings/<recording_id>", methods=["POST"])
@auth.oidc_auth("default")
def update_recording_name(meeting_id, recording_id):
    user = get_current_user()
    meeting = Meeting.query.get(meeting_id) or abort(404)
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


@bp.route("/meeting/new", methods=["GET"])
@auth.oidc_auth("default")
def new_meeting():
    user = get_current_user()
    if not user.can_create_meetings:
        return redirect("/welcome")

    form = MeetingWithRecordForm() if current_app.config["RECORDING"] else MeetingForm()

    return render_template(
        "meeting/wizard.html",
        meeting=None,
        form=form,
        recording=current_app.config["RECORDING"],
    )


@bp.route("/meeting/edit/<int:meeting_id>", methods=["GET"])
@auth.oidc_auth("default")
def edit_meeting(meeting_id):
    user = get_current_user()
    meeting = Meeting.query.get(meeting_id)

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
    return redirect("/welcome")


@bp.route("/meeting/files/<int:meeting_id>", methods=["GET"])
@auth.oidc_auth("default")
def edit_meeting_files(meeting_id):
    user = get_current_user()
    meeting = Meeting.query.get(meeting_id)

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
                print("webdav call failed, we disable user data", flush=True)
                print(exception, flush=True)
                user.disable_nextcloud()

        if user is not None and meeting.user_id == user.id:
            return render_template(
                "meeting/filesform.html",
                meeting=meeting,
                form=form,
                fqdn=current_app.config["SERVER_FQDN"],
                beta=current_app.config["BETA"],
            )
    flash(lazy_gettext("Vous ne pouvez pas modifier cet élément"), "warning")
    return redirect("/welcome")


@bp.route("/meeting/files/<int:meeting_id>/<int:file_id>", methods=["GET"])
@auth.oidc_auth("default")
def download_meeting_files(meeting_id, file_id):
    user = get_current_user()
    meeting = Meeting.query.get(meeting_id)

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
                print("webdav call encountered following exception : %s" % exception)
                flash("Le fichier ne semble pas accessible", "error")
                return redirect("/welcome")
    return redirect("/welcome")


@bp.route("/meeting/files/<int:meeting_id>/toggledownload", methods=["POST"])
@auth.oidc_auth("default")
def toggledownload(meeting_id):
    user = get_current_user()
    data = request.get_json()

    if user is None:
        return redirect("/welcome")
    meeting = Meeting.query.get(meeting_id)
    meeting_file = MeetingFiles.query.get(data["id"])
    if meeting_file is not None and meeting.user_id == user.id:
        meeting_file.is_downloadable = data["value"]
        meeting_file.save()

        return jsonify(status=200, id=data["id"])
    return redirect("/welcome")


@bp.route("/meeting/files/<int:meeting_id>/default", methods=["POST"])
@auth.oidc_auth("default")
def set_meeting_default_file(meeting_id):
    user = get_current_user()
    data = request.get_json()

    meeting = Meeting.query.get(meeting_id)
    if meeting.user_id == user.id:
        actual_default_file = meeting.default_file
        if actual_default_file:
            actual_default_file.is_default = False

        meetingFile = MeetingFiles()
        meeting_file = meetingFile.query.get(data["id"])
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
    DROPZONE_DIR = current_app.config["UPLOAD_DIR"] + "/dropzone/"
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    dropzonePath = os.path.join(
        DROPZONE_DIR + str(user.id) + "-" + meeting_id + "-" + title
    )
    metadata = os.stat(dropzonePath)
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
            "local_path": dropzonePath,
        }
        client.upload_sync(**kwargs)

        meetingFile = MeetingFiles()
        meetingFile.nc_path = nc_path

        meetingFile.title = title
        meetingFile.created_at = date.today()
        meetingFile.meeting_id = meeting_id
    except WebDavException as exception:
        user.disable_nextcloud()
        print("ERROR %s" % exception)
        return jsonify(
            status=500, isfrom="dropzone", msg="La connexion avec Nextcloud est rompue"
        )

    try:
        # test for is_default-file absence at the latest time possible
        meeting = Meeting.query.get(meeting_id)
        if len(meeting.files) == 0 and not meeting.default_file:
            meetingFile.is_default = True
        else:
            meetingFile.is_default = False

        meetingFile.save()
        secret_key = current_app.config["SECRET_KEY"]
        meetingFile.update()
        # file has been associated AND uploaded to nextcloud, we can safely remove it from visio-agent tmp directory
        removeDropzoneFile(dropzonePath)
        return jsonify(
            status=200,
            isfrom="dropzone",
            isDefault=is_default,
            title=meetingFile.short_title,
            id=meetingFile.id,
            created_at=meetingFile.created_at.strftime(
                current_app.config["TIME_FORMAT"]
            ),
        )
    except exc.SQLAlchemyError as error:
        print("ERROR %s" % error)
        return jsonify(status=500, isfrom="dropzone", msg="File already exists")


def add_meeting_file_URL(url, meeting_id, is_default):
    user = get_current_user()
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

    meetingFile = MeetingFiles()

    meetingFile.title = title
    meetingFile.created_at = date.today()
    meetingFile.meeting_id = meeting_id
    meetingFile.url = url
    meetingFile.is_default = is_default

    getFile = requests.get(url)

    try:
        meetingFile.save()
        return jsonify(
            status=200,
            isfrom="url",
            isDefault=is_default,
            title=meetingFile.short_title,
            id=meetingFile.id,
            created_at=meetingFile.created_at.strftime(
                current_app.config["TIME_FORMAT"]
            ),
        )
    except exc.SQLAlchemyError as error:
        print("ERROR %s" % error)
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
    except WebDavException as exception:
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
            msg=f"Fichier {title} TROP VOLUMINEUX, ne pas dépasser 20Mo",
        )

    meetingFile = MeetingFiles()

    meetingFile.title = path
    meetingFile.created_at = date.today()
    meetingFile.meeting_id = meeting_id
    meetingFile.nc_path = path
    meetingFile.is_default = is_default
    secret_key = current_app.config["SECRET_KEY"]

    try:
        meetingFile.save()
        return jsonify(
            status=200,
            isfrom="nextcloud",
            isDefault=is_default,
            title=meetingFile.short_title,
            id=meetingFile.id,
            created_at=meetingFile.created_at.strftime(
                current_app.config["TIME_FORMAT"]
            ),
        )
    except exc.SQLAlchemyError as error:
        print("ERROR %s" % error)
        return jsonify(status=500, isfrom="nextcloud", msg="File already exists")


def add_external_meeting_file_nextcloud(path, meeting_id):
    user = get_current_user()

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
    meeting = Meeting.query.get(meeting_id)

    data = request.get_json()
    is_default = False
    if len(meeting.files) == 0:
        is_default = True
    if meeting.user_id == user.id:
        print(data)
        if data["from"] == "nextcloud":
            print("associating meeting with file from nextcloud")
            return add_meeting_file_nextcloud(data["value"], meeting_id, is_default)
        if data["from"] == "URL":
            print("associating meeting with file from url")
            return add_meeting_file_URL(data["value"], meeting_id, is_default)
        if data["from"] == "dropzone":
            print("associating meeting with file from dropzone")
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

    meeting = Meeting.query.get(meeting_id)
    if meeting and user and meeting.user_id == user.id:
        return upload(user, meeting_id, request.files["dropzoneFiles"])
    else:
        flash("Traitement de requête impossible", "error")
        return redirect("/welcome")


# for dropzone chunk file by file validation
# shamelessly taken from https://stackoverflow.com/questions/44727052/handling-large-file-uploads-with-flask
def upload(user, meeting_id, file):
    DROPZONE_DIR = current_app.config["UPLOAD_DIR"] + "/dropzone/"
    Path(DROPZONE_DIR).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join(
        DROPZONE_DIR,
        secure_filename(str(user.id) + "-" + meeting_id + "-" + file.filename),
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
    meetingFile = MeetingFiles()
    meeting_file = meetingFile.query.get(meeting_file_id)
    meeting = Meeting()
    cur_meeting = meeting.query.get(meeting_file.meeting_id)

    if cur_meeting.user_id == user.id:
        db.session.delete(meeting_file)
        db.session.commit()
        newDefaultId = None
        if meeting_file.is_default:
            cur_meeting = meeting.query.get(meeting_file.meeting_id)
            if len(cur_meeting.files) > 0:
                cur_meeting.files[0].is_default = True
                newDefaultId = cur_meeting.files[0].id
                cur_meeting.save()
        return jsonify(
            status=200,
            newDefaultId=newDefaultId,
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
        return redirect("/welcome")

    if not form.validate():
        flash("Le formulaire contient des erreurs", "error")
        return render_template(
            "meeting/wizard.html",
            meeting=None if is_new_meeting else Meeting.query.get(form.id.data),
            form=form,
            recording=current_app.config["RECORDING"],
        )

    if is_new_meeting:
        meeting = Meeting()
        meeting.user = user
    else:
        meeting_id = form.data["id"]
        meeting = Meeting.query.get(meeting_id)
        del form.id
        del form.name
    if form.data.get("allowStartStopRecording") or form.data.get("autoStartRecording"):
        meeting.record = True
    else:
        meeting.record = False
    form.populate_obj(meeting)
    meeting.save()
    flash(
        lazy_gettext(
            "%(meeting_name)s modifications prises en compte", meeting_name=meeting.name
        ),
        "success",
    )

    if meeting.is_meeting_running():
        end_meeting_form = EndMeetingForm()
        EndMeetingForm.meeting_id.data = meeting.id
        return render_template(
            "meeting/end.html",
            meeting=meeting,
            form=EndMeetingForm(data={"meeting_id": meeting_id}),
        )
    return redirect("/welcome")


@bp.route("/meeting/end", methods=["POST"])
@auth.oidc_auth("default")
def end_meeting():
    user = get_current_user()
    form = EndMeetingForm(request.form)

    meeting_id = form.data["meeting_id"]
    meeting = Meeting.query.get(meeting_id) or abort(404)

    if user == meeting.user:
        meeting.end_bbb()
        flash(
            f"{current_app.config['WORDING_MEETING'].capitalize()} « {meeting.name} » terminé(e)",
            "success",
        )
    return redirect("/welcome")


@bp.route("/meeting/create/<int:meeting_id>", methods=["GET"])
@auth.oidc_auth("default")
def create_meeting(meeting_id):
    user = get_current_user()
    m = Meeting.query.get(meeting_id)
    if m.user_id == user.id:
        m.create_bbb()
        m.save()
    return redirect("/welcome")


# draft for insertDocument calls to BBB API
# @TODO: can we remove this def entirely?
@bp.route("/insertDoc/<token>", methods=["GET"])
def insertDoc(token):
    # select good file from token
    # get file through NC credentials - HOW POSSIBLE ?
    # return file as response to BBB server

    m = MeetingFiles.query.filter_by(download_hash=token).one()
    secret_key = current_app.config["SECRET_KEY"]
    if (
        m
        or m.token
        != hashlib.sha1(f"{secret_key}{m.id}{secret_key}".encode("utf-8")).hexdigest()
    ):
        make_response("NOT OK", 500)

    params = {"meetingID": m.meeting.meetingID}
    action = "insertDocument"
    req = requests.Request(
        "POST",
        "%s/%s" % (current_app.config["BIGBLUEBUTTON_ENDPOINT"], action),
        params=params,
    )
    headers = {"Content-Type": "application/xml"}
    pr = req.prepare()
    bigbluebutton_secret = current_app.config["BIGBLUEBUTTON_SECRET"]
    s = "%s%s" % (
        pr.url.replace("?", "").replace(
            current_app.config["BIGBLUEBUTTON_ENDPOINT"] + "/", ""
        ),
        bigbluebutton_secret,
    )
    params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()

    # xml now use
    xml = f"<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'><document url='{current_app.config['SERVER_FQDN']}/ncdownload/{m.id}/{m.download_hash}' filename='m.title' /> </module></modules>"

    r = requests.post(
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
    meeting = Meeting.query.get(meeting_id)
    if (
        meeting is not None
        and meeting.is_meeting_running() is True
        and user is not None
        and meeting.user_id == user.id
    ):
        return render_template("meeting/externalUpload.html", meeting=meeting)
    else:
        return redirect("/welcome")


@bp.route("/ncdownload/<isexternal>/<mfid>/<mftoken>", methods=["GET"])
# @auth.token_auth(provider_name="default") - must be accessible by BBB serveur, so no auth
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
            f"{secret_key}-{isexternal}-{mfid}-{secret_key}".encode("utf-8")
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
    except WebDavException as exception:
        meeting_file.meeting.user.disable_nextcloud()
        return jsonify(status=500, msg="La connexion avec Nextcloud semble rompue")
    # send the downloaded file to the BBB:
    return send_from_directory(TMP_DOWNLOAD_DIR, uniqfile)


@bp.route(
    "/meeting/signinmail/<meeting_fake_id>/expiration/<expiration>/hash/<h>",
    methods=["GET"],
)
def signin_mail_meeting(meeting_fake_id, expiration, h):
    is_rie = any(
        [
            IPAddress(request.remote_addr) in IPNetwork(network_ip)
            for network_ip in current_app.config["RIE_NETWORK_IPS"]
        ]
    )
    meeting = get_mail_meeting(meeting_fake_id)
    wordings = current_app.config["WORDINGS"]

    if meeting is None:
        flash(
            lazy_gettext(
                "Aucune %(meeting_label)s ne correspond à ces paramètres",
                meeting_label=wordings["meeting_label"],
            ),
            "success",
        )
        return redirect("/")

    hash_matches = meeting.get_mail_signin_hash(meeting_fake_id, expiration) == h
    if not hash_matches:
        flash(lazy_gettext("Lien invalide"), "error")
        return redirect("/")

    is_expired = datetime.fromtimestamp(float(expiration)) < datetime.now()
    if is_expired:
        flash(lazy_gettext("Lien expiré"), "error")
        return redirect("/")

    return render_template(
        "meeting/joinmail.html",
        meeting=meeting,
        meeting_fake_id=meeting.fake_id,
        expiration=expiration,
        user_id="fakeuserId",
        h=h,
        is_rie=is_rie,
        role="moderator",
    )


@bp.route(
    "/meeting/signin/<meeting_fake_id>/creator/<int:user_id>/hash/<h>", methods=["GET"]
)
def signin_meeting(meeting_fake_id, user_id, h):
    is_rie = any(
        [
            IPAddress(request.remote_addr) in IPNetwork(network_ip)
            for network_ip in current_app.config["RIE_NETWORK_IPS"]
        ]
    )
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    wordings = current_app.config["WORDINGS"]
    if meeting is None:
        flash(
            lazy_gettext(
                "Aucune %(meeting_label)s ne correspond à ces paramètres",
                meeting_label=wordings["meeting_label"],
            ),
            "success",
        )
        return redirect("/")

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)

    if role == "authenticated":
        return redirect(
            url_for("routes.join_meeting_as_authenticated", meeting_id=meeting_fake_id)
        )
    elif not role:
        return redirect("/")
    return render_template(
        "meeting/join.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        user_id=user_id,
        h=h,
        is_rie=is_rie,
        role=role,
    )


@bp.route(
    "/meeting/auth/<meeting_fake_id>/creator/<int:user_id>/hash/<h>", methods=["GET"]
)
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
    "/meeting/wait/<meeting_fake_id>/creator/<int:user_id>/hash/<h>/fullname/<path:fullname>/fullname_suffix/",
    methods=["GET"],
    defaults={"fullname_suffix": ""},
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<int:user_id>/hash/<h>/fullname/<path:fullname>/fullname_suffix/<path:fullname_suffix>",
    methods=["GET"],
)
def waiting_meeting(meeting_fake_id, user_id, h, fullname, fullname_suffix):
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    if meeting is None:
        return redirect("/")

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)
    if not role:
        return redirect("/")
    return render_template(
        "meeting/join.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        user_id=user_id,
        h=h,
        role=role,
        fullname=fullname,
        fullname_suffix=fullname_suffix,
        retry_join_meeting=retry_join_meeting(
            request.referrer, role, fullname, fullname_suffix
        ),
    )


@bp.route("/meeting/join", methods=["POST"])
def join_meeting():
    form = JoinMeetingForm(request.form)
    if not form.validate():
        return redirect("/")
    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    user_id = form["user_id"].data
    h = form["h"].data
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    if meeting is None:
        return redirect("/")

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)
    fullname_suffix = form["fullname_suffix"].data
    if role == "authenticated":
        fullname = get_authenticated_attendee_fullname()
    elif not role:
        return redirect("/")
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
        return redirect("/")
    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    user_id = form["user_id"].data
    expiration = form["expiration"].data
    h = form["h"].data

    meeting = get_mail_meeting(meeting_fake_id)
    if meeting is None:
        flash(
            lazy_gettext(
                "%(meeting_label)s inexistante",
                meeting_label=current_app.config["WORDINGS"][
                    "meeting_label"
                ].capitalize(),
            ),
            "error",
        )
        return redirect("/")

    hash_matches = meeting.get_mail_signin_hash(meeting_fake_id, expiration) == h
    if not hash_matches:
        flash(lazy_gettext("Lien invalide"), "error")
        return redirect("/")

    is_expired = datetime.fromtimestamp(expiration) < datetime.now()
    if is_expired:
        flash(lazy_gettext("Lien expiré"), "error")
        return redirect("/")

    return redirect(meeting.get_join_url("moderator", fullname, create=True))


def get_authenticated_attendee_fullname():
    attendee_session = UserSession(session)
    attendee_info = attendee_session.userinfo
    given_name = attendee_info["given_name"]
    family_name = attendee_info["family_name"]
    fullname = f"{given_name} {family_name}"
    return fullname


@bp.route("/meeting/join/<int:meeting_id>/authenticated", methods=["GET"])
@auth.oidc_auth("attendee")
def join_meeting_as_authenticated(meeting_id):
    meeting = Meeting.query.get(meeting_id) or abort(404)
    role = "authenticated"
    fullname = get_authenticated_attendee_fullname()
    return redirect(
        url_for(
            "routes.waiting_meeting",
            meeting_fake_id=meeting_id,
            user_id=meeting.user.id,
            h=meeting.get_hash(role),
            fullname=fullname,
            fullname_suffix="",
        )
    )


@bp.route("/meeting/join/<int:meeting_id>/<role>", methods=["GET"])
@auth.oidc_auth("default")
def join_meeting_as_role(meeting_id, role):
    user = get_current_user()
    form = JoinMeetingAsRoleForm(data={"meeting_id": meeting_id, "role": role})
    if not form.validate():
        abort(404)
    meeting = Meeting.query.get(meeting_id) or abort(404)
    if meeting.user_id == user.id:
        return redirect(meeting.get_join_url(role, user.fullname, create=True))
    else:
        flash(lazy_gettext("Accès non autorisé"), "error")
        return redirect("/")


@bp.route("/meeting/delete", methods=["POST", "GET"])
@auth.oidc_auth("default")
def delete_meeting():
    if request.method == "POST":
        user = get_current_user()
        meeting_id = request.form["id"]
        meeting = Meeting.query.get(meeting_id)

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
                    + " : {message}".format(code=return_code, message=message),
                    "error",
                )
            else:
                db.session.delete(meeting)
                db.session.commit()
                flash(lazy_gettext("Élément supprimé"), "success")
        else:
            flash(lazy_gettext("Vous ne pouvez pas supprimer cet élément"), "error")
    return redirect("/welcome")


@bp.route("/meeting/video/delete", methods=["POST"])
@auth.oidc_auth("default")
def delete_video_meeting():
    if request.method == "POST":
        user = get_current_user()
        meeting_id = request.form["id"]
        meeting = Meeting.query.get(meeting_id)
        if meeting.user_id == user.id:
            recordID = request.form["recordID"]
            data = meeting.delete_recordings(recordID)
            return_code = data.get("returncode")
            if return_code == "SUCCESS":
                flash(lazy_gettext("Vidéo supprimée"), "success")
            else:
                message = data.get("message", "")
                flash(
                    lazy_gettext(
                        "Nous n'avons pas pu supprimer cette vidéo : %(code)s, %(message)s",
                        code=return_code,
                        message=message,
                    ),
                    "error",
                )
        else:
            flash(
                lazy_gettext("Vous ne pouvez pas supprimer cette enregistrement"),
                "error",
            )
    return redirect("/welcome")


@bp.route("/logout")
@auth.oidc_logout
def logout():
    return redirect("/")


@current_app.errorhandler(403)
def page_not_authorized(e):
    return (
        render_template(
            "errors/403.html",
        ),
        403,
    )


@current_app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "errors/404.html",
        ),
        404,
    )


@current_app.errorhandler(500)
def page_error(e):
    return (
        render_template(
            "errors/500.html",
        ),
        500,
    )
