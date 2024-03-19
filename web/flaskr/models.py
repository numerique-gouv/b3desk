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
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from xml.etree import ElementTree

import requests
from flask import current_app
from flask import render_template
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flaskr.tasks import background_upload
from flaskr.utils import secret_key
from sqlalchemy_utils import EncryptedType


db = SQLAlchemy()

MODERATOR_ONLY_MESSAGE_MAXLENGTH = 150


def sigchld_handler():
    os.wait()
    print("ok")


def get_user_nc_credentials(username):
    if (
        not current_app.config["NC_LOGIN_API_KEY"]
        or not current_app.config["NC_LOGIN_API_URL"]
        or not current_app.config["FILE_SHARING"]
        or not username
    ):
        print(
            "File sharing deactivated or unable to perform, no connection to Nextcloud instance"
        )
        return {"nctoken": None, "nclocator": None, "nclogin": None}
    postData = {"username": username}
    postHeaders = {"X-API-KEY": current_app.config["NC_LOGIN_API_KEY"]}
    print(
        "Retrieve NC credentials from NC_LOGIN_API_URL %s "
        % current_app.config["NC_LOGIN_API_URL"]
    )
    try:
        response = requests.post(
            current_app.config["NC_LOGIN_API_URL"], json=postData, headers=postHeaders
        )
        data = response.json()
        return data
    except requests.exceptions.RequestException:
        print("Cannot contact NC, returning None values")
        return {"nctoken": None, "nclocator": None, "nclogin": None}


def get_or_create_user(user_info):
    # preferred_username is login from keycloak, REQUIRED for nc_login connexion
    # data is conveyed like following :
    # user logs in to keycloak
    # visio-agent retrives preferred_username from keycloack ( aka keycloak LOGIN, which is immutable )
    # visio-agent calls EDNAT API for NC_DATA retrieval, passing LOGIN as postData
    # visio-agent can now connect to remote NC with NC_DATA
    if current_app.config["FILE_SHARING"]:
        preferred_username = user_info["preferred_username"]
    else:
        preferred_username = None
    given_name = user_info["given_name"]
    family_name = user_info["family_name"]
    email = user_info["email"].lower()

    user = User.query.filter_by(email=email).first()

    if user is None:
        data = get_user_nc_credentials(preferred_username)
        nc_locator, nc_token, nc_login = (
            data["nclocator"],
            data["nctoken"],
            preferred_username,
        )
        if nc_locator is None or nc_login is None or nc_token is None:
            nc_last_auto_enroll = None
        else:
            nc_last_auto_enroll = datetime.now().strftime(
                current_app.config["TIME_FORMAT"]
            )
        user = User(
            email=email,
            given_name=given_name,
            family_name=family_name,
            nc_locator=nc_locator,
            nc_login=nc_login,
            nc_token=nc_token,
            nc_last_auto_enroll=nc_last_auto_enroll,
            last_connection_utc_datetime=datetime.utcnow(),
        )
        user.save()
    else:
        user_has_changed = False
        if (
            not user.nc_last_auto_enroll
            or not user.nc_locator
            or not user.nc_token
            or (
                (datetime.now() - user.nc_last_auto_enroll).days
                > current_app.config["NC_LOGIN_TIMEDELTA_DAYS"]
            )
        ):
            data = get_user_nc_credentials(preferred_username)
            nc_locator, nc_token, nc_login = (
                data["nclocator"],
                data["nctoken"],
                preferred_username,
            )
            if nc_locator is None or nc_login is None or nc_token is None:
                nc_last_auto_enroll = None
            else:
                nc_last_auto_enroll = datetime.now().strftime(
                    current_app.config["TIME_FORMAT"]
                )
            user.nc_token = nc_token
            user.nc_login = nc_login
            user.nc_locator = nc_locator
            user.nc_last_auto_enroll = nc_last_auto_enroll
            user_has_changed = True

        if user.given_name != given_name:
            user.given_name = given_name
            user_has_changed = True
        if user.family_name != family_name:
            user.family_name = family_name
            user_has_changed = True
        if (
            not user.last_connection_utc_datetime
            or user.last_connection_utc_datetime.date() < date.today()
        ):
            user.last_connection_utc_datetime = datetime.utcnow()
            user_has_changed = True
        if user_has_changed:
            user.save()
    return user


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(150), unique=True)
    given_name = db.Column(db.Unicode(50))
    family_name = db.Column(db.Unicode(50))
    nc_locator = db.Column(db.Unicode(255))
    nc_login = db.Column(db.Unicode(255))
    nc_token = db.Column(db.Unicode(255))
    nc_last_auto_enroll = db.Column(db.DateTime)
    last_connection_utc_datetime = db.Column(db.DateTime)

    meetings = db.relationship("Meeting", back_populates="user")

    @property
    def fullname(self):
        return f"{self.given_name} {self.family_name}"

    @property
    def hash(self):
        s = f"{self.email}|{secret_key()}"
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    @property
    def can_create_meetings(self):
        return len(self.meetings) < current_app.config["MAX_MEETINGS_PER_USER"]

    def save(self):
        db.session.add(self)
        db.session.commit()

    def disable_nextcloud(self):
        self.nc_login = None
        self.nc_locator = None
        self.nc_token = None
        self.nc_last_auto_enroll = None
        self.save()


class BBB:
    """Interface to BBB API"""

    def __init__(self, meeting):
        self.meeting = meeting

    def get_params_with_checksum(self, action, params):
        request = requests.Request(
            "GET",
            "{}/{}".format(current_app.config["BIGBLUEBUTTON_ENDPOINT"], action),
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
        return params

    def get_url(self, action):
        bbb_endpoint = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
        return f"{bbb_endpoint}/{action}"

    def is_meeting_running(self):
        action = "isMeetingRunning"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        r = requests.get(self.get_url(action), params=params)
        d = {c.tag: c.text for c in ElementTree.fromstring(r.content)}
        return d and d["returncode"] == "SUCCESS" and d["running"] == "true"

    def insertDocsNoDefault(self):
        # meeting has started, we can now add files by using insertDocument API
        # ADDING ALL FILES EXCEPT DEFAULT
        SERVER_FQDN = current_app.config["SERVER_FQDN"]
        SECRET_KEY = current_app.config["SECRET_KEY"]
        BIGBLUEBUTTON_ENDPOINT = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
        BIGBLUEBUTTON_SECRET = current_app.config["BIGBLUEBUTTON_SECRET"]

        insertAction = "insertDocument"
        xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
        xml_end = " </module></modules>"
        xml_mid = ""
        for meeting_file in self.meeting.files:
            if meeting_file.is_default:
                continue
            elif meeting_file.url:
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
            else:  # file is not URL hence it was uploaded to nextcloud:
                filehash = hashlib.sha1(
                    f"{SECRET_KEY}-0-{meeting_file.id}-{SECRET_KEY}".encode()
                ).hexdigest()
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{SERVER_FQDN}/ncdownload/0/{meeting_file.id}/{filehash}' filename='{meeting_file.title}' />"

        xml = xml_beg + xml_mid + xml_end
        params = {"meetingID": self.meeting.meetingID}
        request = requests.Request(
            "POST",
            f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}",
            params=params,
        )
        pr = request.prepare()
        bigbluebutton_secret = BIGBLUEBUTTON_SECRET
        s = "{}{}".format(
            pr.url.replace("?", "").replace(BIGBLUEBUTTON_ENDPOINT + "/", ""),
            bigbluebutton_secret,
        )
        params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()

        requests.post(
            f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}",
            headers={"Content-Type": "application/xml"},
            data=xml,
            params=params,
        )
        return {}

    def create(self):
        action = "create"
        insertAction = "insertDocument"
        params = {
            "meetingID": self.meeting.meetingID,
            "name": self.meeting.name,
            "uploadExternalUrl": current_app.config["SERVER_FQDN"]
            + "/meeting/"
            + str(self.meeting.id)
            + "/externalUpload",
            "uploadExternalDescription": current_app.config[
                "EXTERNAL_UPLOAD_DESCRIPTION"
            ],
        }
        if (param := self.meeting.record) is not None:
            params["record"] = str(param).lower()
        if (param := self.meeting.autoStartRecording) is not None:
            params["autoStartRecording"] = str(param).lower()
        if (param := self.meeting.allowStartStopRecording) is not None:
            params["allowStartStopRecording"] = str(param).lower()
        if (param := self.meeting.webcamsOnlyForModerator) is not None:
            params["webcamsOnlyForModerator"] = str(param).lower()
        if (param := self.meeting.muteOnStart) is not None:
            params["muteOnStart"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisableCam) is not None:
            params["lockSettingsDisableCam"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisableMic) is not None:
            params["lockSettingsDisableMic"] = str(param).lower()
        if (param := self.meeting.allowModsToUnmuteUsers) is not None:
            params["allowModsToUnmuteUsers"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisablePrivateChat) is not None:
            params["lockSettingsDisablePrivateChat"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisablePublicChat) is not None:
            params["lockSettingsDisablePublicChat"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisableNote) is not None:
            params["lockSettingsDisableNote"] = str(param).lower()
        if param := self.meeting.attendeePW:
            params["attendeePW"] = param
        if param := self.meeting.moderatorPW:
            params["moderatorPW"] = param
        if param := self.meeting.welcome:
            params["welcome"] = param
        if param := self.meeting.maxParticipants:
            params["maxParticipants"] = str(param)
        if param := self.meeting.logoutUrl:
            params["logoutURL"] = param
        if param := self.meeting.duration:
            params["duration"] = str(param)
        bigbluebutton_analytics_callback_url = current_app.config[
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
        ]
        if bigbluebutton_analytics_callback_url:
            # bbb will call this endpoint when meeting ends
            params.update(
                {
                    "meetingKeepEvents": "true",
                    "meta_analytics-callback-url": bigbluebutton_analytics_callback_url,
                }
            )
        if self.meeting.attendeePW is None:
            # if no attendeePW it a meeting create with a mail (not logged in)
            params["moderatorOnlyMessage"] = render_template(
                "meeting/signin_mail_link.html",
                main_message=self.meeting.moderatorOnlyMessage,
                link=self.meeting.get_mail_signin_url(),
            )
        else:
            quick_meeting_moderator_link_introduction = current_app.config[
                "QUICK_MEETING_MODERATOR_LINK_INTRODUCTION"
            ]
            quick_meeting_attendee_link_introduction = current_app.config[
                "QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION"
            ]
            params["moderatorOnlyMessage"] = render_template(
                "meeting/signin_links.html",
                moderator_message=self.meeting.moderatorOnlyMessage,
                moderator_link_introduction=quick_meeting_moderator_link_introduction,
                moderator_signin_url=self.meeting.get_signin_url("moderator"),
                attendee_link_introduction=quick_meeting_attendee_link_introduction,
                attendee_signin_url=self.meeting.get_signin_url("attendee"),
            )
        params["guestPolicy"] = (
            "ASK_MODERATOR" if self.meeting.guestPolicy else "ALWAYS_ACCEPT"
        )

        params = self.get_params_with_checksum(action, params)
        if current_app.config["FILE_SHARING"]:
            # ADDING DEFAULT FILE TO MEETING
            SECRET_KEY = current_app.config["SECRET_KEY"]
            xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
            xml_end = " </module></modules>"
            xml_mid = ""

            if self.meeting.default_file:
                meeting_file = self.meeting.default_file
                if meeting_file.url:
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
                else:  # file is not URL nor NC hence it was uploaded
                    filehash = hashlib.sha1(
                        f"{SECRET_KEY}-0-{meeting_file.id}-{SECRET_KEY}".encode()
                    ).hexdigest()
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{current_app.config['SERVER_FQDN']}/ncdownload/0/{meeting_file.id}/{filehash}' filename='{meeting_file.title}' />"

            xml = xml_beg + xml_mid + xml_end
            r = requests.post(
                self.get_url(action),
                params=params,
                headers={"Content-Type": "application/xml"},
                data=xml if self.meeting.default_file else None,
            )
            ## BEGINNING OF TASK CELERY - aka background_upload for meeting_files
            params = {}
            xml = ""
            # ADDING ALL FILES EXCEPT DEFAULT
            non_default_meeting_files = [
                meeting_file
                for meeting_file in self.meeting.files
                if not meeting_file.is_default
            ]
            if non_default_meeting_files:
                SERVER_FQDN = current_app.config["SERVER_FQDN"]
                BIGBLUEBUTTON_ENDPOINT = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
                BIGBLUEBUTTON_SECRET = current_app.config["BIGBLUEBUTTON_SECRET"]

                insertAction = "insertDocument"
                xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
                xml_end = " </module></modules>"
                xml_mid = ""
                for meeting_file in non_default_meeting_files:
                    if meeting_file.url:
                        xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
                    else:  # file is not URL nor NC hence it was uploaded
                        filehash = hashlib.sha1(
                            f"{SECRET_KEY}-0-{meeting_file.id}-{SECRET_KEY}".encode()
                        ).hexdigest()
                        xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{SERVER_FQDN}/ncdownload/0/{meeting_file.id}/{filehash}' filename='{meeting_file.title}' />"

                xml = xml_beg + xml_mid + xml_end
                params = {"meetingID": self.meeting.meetingID}
                request = requests.Request(
                    "POST",
                    f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}",
                    params=params,
                )
                pr = request.prepare()
                bigbluebutton_secret = BIGBLUEBUTTON_SECRET
                s = "{}{}".format(
                    pr.url.replace("?", "").replace(BIGBLUEBUTTON_ENDPOINT + "/", ""),
                    bigbluebutton_secret,
                )
                params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()
                background_upload.delay(
                    f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}", xml, params
                )

            d = {c.tag: c.text for c in ElementTree.fromstring(r.content)}
            return d
        else:
            r = requests.post(self.get_url(action), params=params)
            d = {c.tag: c.text for c in ElementTree.fromstring(r.content)}
            return d

    def delete_recordings(self, recording_ids):
        """DeleteRecordings BBB API: https://docs.bigbluebutton.org/dev/api.html#deleterecordings"""
        action = "deleteRecordings"
        params = self.get_params_with_checksum(action, {"recordID": recording_ids})
        response = requests.get(self.get_url(action), params=params)
        d = {
            child.tag: child.text for child in ElementTree.fromstring(response.content)
        }
        return d

    def get_meeting_info(self):
        action = "getMeetingInfo"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        resp = requests.get(self.get_url(action), params=params)
        return {c.tag: c.text for c in ElementTree.fromstring(resp.content)}

    def get_recordings(self):
        action = "getRecordings"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        response = requests.get(self.get_url(action), params=params)
        root = ElementTree.fromstring(response.content)
        return_code = root.find("returncode").text
        recordings = root.find("recordings")
        result = []
        if return_code != "FAILED":
            try:
                for recording in recordings.iter("recording"):
                    d = {}
                    d["recordID"] = recording.find("recordID").text
                    name = recording.find("metadata").find("name")
                    d["name"] = name.text if name is not None else None
                    d["participants"] = int(recording.find("participants").text)
                    d["playbacks"] = {}
                    playback = recording.find("playback")
                    for format in playback.iter("format"):
                        images = []
                        preview = format.find("preview")
                        if preview is not None:
                            for i in (
                                format.find("preview").find("images").iter("image")
                            ):
                                image = {k: v for k, v in i.attrib.items()}
                                image["url"] = i.text
                                images.append(image)
                        type = format.find("type").text
                        if type in ("presentation", "video"):
                            d["playbacks"][type] = {
                                "url": format.find("url").text,
                                "images": images,
                            }
                    d["start_date"] = datetime.fromtimestamp(
                        int(recording.find("startTime").text) / 1000.0, tz=timezone.utc
                    ).replace(microsecond=0)
                    result.append(d)
            except Exception as e:
                print(e)
        return result

    def update_recordings(self, recording_ids, metadata):
        """updateRecordings BBB API: https://docs.bigbluebutton.org/dev/api.html#updaterecordings"""
        action = "updateRecordings"
        meta = {f"meta_{key}": value for (key, value) in metadata.items()}
        params = self.get_params_with_checksum(
            action, {"recordID": ",".join(recording_ids), **meta}
        )
        response = requests.get(self.get_url(action), params=params)
        d = {
            child.tag: child.text for child in ElementTree.fromstring(response.content)
        }
        return d

    def prepare_request_to_join_bbb(self, meeting_role, fullname):
        """Join BBB API: https://docs.bigbluebutton.org/dev/api.html#join"""
        params = {
            "fullName": fullname,
            "meetingID": self.meeting.meetingID,
            "redirect": "true",
        }
        if meeting_role == "attendee":
            params["role"] = "viewer"
            params["guest"] = "true"
        elif meeting_role == "authenticated":
            params["role"] = "viewer"
        elif meeting_role == "moderator":
            params["role"] = "moderator"
        action = "join"
        params = self.get_params_with_checksum(action, params)
        request = requests.Request("GET", self.get_url(action), params=params)
        pr = request.prepare()
        return pr

    def end(self):
        action = "end"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        requests.get(self.get_url(action), params=params)


class MeetingFiles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(4096))
    url = db.Column(db.Unicode(4096))
    nc_path = db.Column(db.Unicode(4096))
    meeting_id = db.Column(db.Integer, db.ForeignKey("meeting.id"), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    is_downloadable = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.Date)

    meeting = db.relationship("Meeting", back_populates="files")

    @property
    def short_title(self):
        return (
            self.title
            if len(self.title) < 70
            else f"{self.title[:30]}...{self.title[-30:]}"
        )

    def update(self):
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()


class MeetingFilesExternal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(4096))
    nc_path = db.Column(db.Unicode(4096))
    meeting_id = db.Column(db.Integer, db.ForeignKey("meeting.id"), nullable=False)

    meeting = db.relationship("Meeting", back_populates="externalFiles")

    def update(self):
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="meetings")
    files = db.relationship("MeetingFiles", back_populates="meeting")
    externalFiles = db.relationship("MeetingFilesExternal", back_populates="meeting")

    # BBB params
    name = db.Column(db.Unicode(150))
    attendeePW = db.Column(EncryptedType(db.Unicode(50), secret_key()))
    moderatorPW = db.Column(EncryptedType(db.Unicode(50), secret_key()))
    welcome = db.Column(db.UnicodeText())
    dialNumber = db.Column(db.Unicode(50))
    voiceBridge = db.Column(db.Unicode(50))
    maxParticipants = db.Column(db.Integer)
    logoutUrl = db.Column(db.Unicode(250))
    record = db.Column(db.Boolean, unique=False, default=True)
    duration = db.Column(db.Integer)
    moderatorOnlyMessage = db.Column(db.Unicode(MODERATOR_ONLY_MESSAGE_MAXLENGTH))
    autoStartRecording = db.Column(db.Boolean, unique=False, default=True)
    allowStartStopRecording = db.Column(db.Boolean, unique=False, default=True)
    webcamsOnlyForModerator = db.Column(db.Boolean, unique=False, default=True)
    muteOnStart = db.Column(db.Boolean, unique=False, default=True)
    lockSettingsDisableCam = db.Column(db.Boolean, unique=False, default=True)
    lockSettingsDisableMic = db.Column(db.Boolean, unique=False, default=True)
    allowModsToUnmuteUsers = db.Column(db.Boolean, unique=False, default=False)
    lockSettingsDisablePrivateChat = db.Column(db.Boolean, unique=False, default=True)
    lockSettingsDisablePublicChat = db.Column(db.Boolean, unique=False, default=True)
    lockSettingsDisableNote = db.Column(db.Boolean, unique=False, default=True)
    guestPolicy = db.Column(db.Boolean, unique=False, default=True)
    logo = db.Column(db.Unicode(200))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User")

    _bbb = None

    @property
    def bbb(self):
        if not self._bbb:
            self._bbb = BBB(self)
        return self._bbb

    @property
    def default_file(self):
        for mfile in self.files:
            if mfile.is_default:
                return mfile
        return None

    @property
    def meetingID(self):
        if self.id is not None:
            fid = "meeting-persistent-%i" % (self.id)
        else:
            fid = "meeting-vanish-%s" % (self.fake_id)
        return "{}--{}".format(fid, self.user.hash if self.user else "")

    @property
    def fake_id(self):
        if self.id is not None:
            return self.id
        else:
            try:
                return self._fake_id
            except:
                return None

    @fake_id.setter
    def fake_id(self, fake_value):
        self._fake_id = fake_value

    @fake_id.deleter
    def fake_id(self):
        del self._fake_id

    def get_hash(self, role):
        s = f"{self.meetingID}|{self.attendeePW}|{self.name}|{role}"
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    def is_meeting_running(self):
        return self.bbb.is_meeting_running()

    def create_bbb(self):
        result = self.bbb.create()
        if result and result["returncode"] == "SUCCESS":
            if self.id is None:
                self.attendeePW = result["attendeePW"]
                self.moderatorPW = result["moderatorPW"]
        return result if result else {}

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete_recordings(self, recording_ids):
        return self.bbb.delete_recordings(recording_ids)

    def delete_all_recordings(self):
        recordings = self.get_recordings()
        if not recordings:
            return {}
        recording_ids = ",".join(
            [recording.get("recordID", "") for recording in recordings]
        )
        return self.delete_recordings(recording_ids)

    def get_recordings(self):
        return self.bbb.get_recordings()

    def update_recording_name(self, recording_id, name):
        return self.bbb.update_recordings(
            recording_ids=[recording_id], metadata={"name": name}
        )

    def get_join_url(self, meeting_role, fullname, fullname_suffix="", create=False):
        is_meeting_available = self.is_meeting_running()
        should_create_room = (
            not is_meeting_available and (meeting_role == "moderator") and create
        )
        if should_create_room:
            d = self.create_bbb()
            if "returncode" in d and d["returncode"] == "SUCCESS":
                is_meeting_available = True
        if is_meeting_available:
            nickname = (
                f"{fullname} - {fullname_suffix}" if fullname_suffix else fullname
            )
            return self.bbb.prepare_request_to_join_bbb(meeting_role, nickname).url
        return url_for(
            "routes.waiting_meeting",
            meeting_fake_id=self.fake_id,
            user_id=self.user.id,
            h=self.get_hash(meeting_role),
            fullname=fullname,
            fullname_suffix=fullname_suffix,
        )

    def get_signin_url(self, meeting_role):
        return current_app.config["SERVER_FQDN"] + url_for(
            "routes.signin_meeting",
            meeting_fake_id=self.fake_id,
            user_id=self.user.id,
            h=self.get_hash(meeting_role),
        )

    def get_mail_signin_hash(self, meeting_id, expiration_epoch):
        s = f"{meeting_id}-{expiration_epoch}"
        return hashlib.sha256(
            s.encode("utf-8") + secret_key().encode("utf-8")
        ).hexdigest()

    def get_mail_signin_url(self):
        expiration = str((datetime.now() + timedelta(weeks=1)).timestamp()).split(".")[
            0
        ]  # remove milliseconds
        hash_param = self.get_mail_signin_hash(self.fake_id, expiration)
        return current_app.config["SERVER_FQDN"] + url_for(
            "routes.signin_mail_meeting",
            meeting_fake_id=self.fake_id,
            expiration=expiration,
            h=hash_param,
        )

    def get_data_as_dict(self, fullname, fetch_recording=False):
        if self.id is None:
            d = {}
        else:
            d = {
                c.name: getattr(self, c.name)
                for c in self.__table__.columns
                if c.name != "slideshows"
            }
            if fetch_recording:
                d["recordings"] = self.get_recordings()
            d["running"] = self.is_meeting_running()
            d["attendee_signin_url"] = self.get_signin_url("attendee")
            d["moderator_signin_url"] = self.get_signin_url("moderator")
            d["authenticated_attendee_signin_url"] = self.get_signin_url(
                "authenticated"
            )
        d["moderator_join_url"] = self.get_join_url("moderator", fullname)
        d["attendee_join_url"] = self.get_join_url("attendee", fullname)
        return d

    def get_role(self, hashed_role, user_id=None):
        if user_id and self.user.id == user_id:
            return "moderator"
        elif self.get_hash("attendee") == hashed_role:
            role = "attendee"
        elif self.get_hash("moderator") == hashed_role:
            role = "moderator"
        elif self.get_hash("authenticated") == hashed_role:
            role = (
                "authenticated"
                if current_app.config["OIDC_ATTENDEE_ENABLED"]
                else "attendee"
            )
        else:
            role = None
        return role

    def end_bbb(self):
        self.bbb.end()
