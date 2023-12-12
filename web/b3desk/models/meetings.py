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
from datetime import datetime
from datetime import timedelta

from b3desk.utils import secret_key
from flask import current_app
from flask import url_for
from sqlalchemy_utils import StringEncryptedType

from . import db
from .bbb import BBB

MODERATOR_ONLY_MESSAGE_MAXLENGTH = 150


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
    attendeePW = db.Column(StringEncryptedType(db.Unicode(50), secret_key()))
    moderatorPW = db.Column(StringEncryptedType(db.Unicode(50), secret_key()))
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
