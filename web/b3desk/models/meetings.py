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
import hashlib
import random
from datetime import datetime
from datetime import timedelta

from flask import current_app
from flask import url_for
from flask_babel import lazy_gettext as _
from sqlalchemy_utils import StringEncryptedType
from wtforms import ValidationError

from b3desk.utils import get_random_alphanumeric_string
from b3desk.utils import secret_key

from . import db
from .roles import Role
from .users import User

MODERATOR_ONLY_MESSAGE_MAXLENGTH = 150


class BaseMeetingFiles:
    def __init__(self, id=None, title=None, nc_path=None, meeting_id=None, **kwargs):
        self.id = id
        self.title = title
        self.nc_path = nc_path
        self.meeting_id = meeting_id
        super().__init__(**kwargs)


class MeetingFiles(BaseMeetingFiles, db.Model):
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


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    is_favorite = db.Column(db.Boolean, unique=False, default=False)
    user = db.relationship("User", back_populates="meetings")
    files = db.relationship("MeetingFiles", back_populates="meeting")
    last_connection_utc_datetime = db.Column(db.DateTime)
    is_shadow = db.Column(db.Boolean, unique=False, default=False)
    visio_code = db.Column(db.Unicode(50), unique=True, nullable=False)

    # BBB params
    name = db.Column(db.Unicode(150))
    attendeePW = db.Column(StringEncryptedType(db.Unicode(50), secret_key()))
    moderatorPW = db.Column(StringEncryptedType(db.Unicode(50), secret_key()))
    welcome = db.Column(db.UnicodeText())
    dialNumber = db.Column(db.Unicode(50))
    voiceBridge = db.Column(db.Unicode(50), unique=True, nullable=False)
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
        from .bbb import BBB

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
    def non_default_files(self):
        return [
            meeting_file for meeting_file in self.files if not meeting_file.is_default
        ]

    @property
    def meetingID(self):
        if self.id is not None:
            fid = f"meeting-persistent-{self.id}"
        else:
            fid = f"meeting-vanish-{self.fake_id}"
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

    def get_hash(self, role: Role, hash_from_string=False):
        s = f"{self.meetingID}|{self.attendeePW}|{self.name}|{role.name if hash_from_string else role}"
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    def is_running(self):
        data = self.bbb.is_meeting_running()
        return data and data["returncode"] == "SUCCESS" and data["running"] == "true"

    def create_bbb(self):
        self.voiceBridge = (
            pin_generation() if not self.voiceBridge else self.voiceBridge
        )
        result = self.bbb.create()
        if result and result.get("returncode", "") == "SUCCESS":
            if self.id is None:
                self.attendeePW = result["attendeePW"]
                self.moderatorPW = result["moderatorPW"]
            if (
                current_app.config["ENABLE_PIN_MANAGEMENT"]
                and self.voiceBridge != result["voiceBridge"]
            ):
                current_app.logger.error(
                    "Voice bridge seems managed by Scalelite or BBB, B3Desk database has different values: voice bridge sent '%s' received '%s'",
                    self.voiceBridge,
                    result["voiceBridge"],
                )
        else:
            current_app.logger.warning(
                "BBB room has not been properly created: %s", result
            )

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

    def get_join_url(
        self,
        meeting_role: Role,
        fullname,
        fullname_suffix="",
        create=False,
        quick_meeting=False,
    ):
        """Return the URL of the BBB meeting URL if available, and the URL of the b3desk 'waiting_meeting' if it is not ready."""
        is_meeting_available = self.is_running()
        should_create_room = (
            not is_meeting_available and (meeting_role == Role.moderator) and create
        )
        if should_create_room:
            current_app.logger.info(
                "Request BBB room creation %s %s", self.name, self.id
            )
            data = self.create_bbb()
            if data.get("returncode", "") == "SUCCESS":
                is_meeting_available = True
                if not quick_meeting:
                    self.last_connection_utc_datetime = datetime.now()
                    self.save()

        if is_meeting_available:
            nickname = (
                f"{fullname} - {fullname_suffix}" if fullname_suffix else fullname
            )
            return self.bbb.prepare_request_to_join_bbb(meeting_role, nickname).url

        return url_for(
            "join.waiting_meeting",
            meeting_fake_id=self.fake_id,
            creator=self.user,
            h=self.get_hash(meeting_role),
            fullname=fullname,
            fullname_suffix=fullname_suffix,
        )

    def get_signin_url(self, meeting_role: Role):
        return url_for(
            "join.signin_meeting",
            meeting_fake_id=self.fake_id,
            creator=self.user,
            h=self.get_hash(meeting_role),
            role=meeting_role,
            _external=True,
            _scheme=current_app.config["PREFERRED_URL_SCHEME"],
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
        return url_for(
            "join.signin_mail_meeting",
            meeting_fake_id=self.fake_id,
            expiration=expiration,
            h=hash_param,
            _external=True,
        )

    def get_role(self, hashed_role, user_id=None) -> Role | None:
        if user_id and self.user.id == user_id:
            return Role.moderator
        elif hashed_role in [
            self.get_hash(Role.attendee),
            self.get_hash(Role.attendee, hash_from_string=True),
        ]:
            role = Role.attendee
        elif hashed_role in [
            self.get_hash(Role.moderator),
            self.get_hash(Role.moderator, hash_from_string=True),
        ]:
            role = Role.moderator
        elif hashed_role in [
            self.get_hash(Role.authenticated),
            self.get_hash(Role.authenticated, hash_from_string=True),
        ]:
            role = (
                Role.authenticated
                if current_app.config["OIDC_ATTENDEE_ENABLED"]
                else Role.attendee
            )
        else:
            role = None
        return role

    def end_bbb(self):
        data = self.bbb.end()
        return data and data["returncode"] == "SUCCESS"


class PreviousVoiceBridge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voiceBridge = db.Column(db.Unicode(50), unique=True, nullable=False)
    archived_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()


def get_all_previous_voiceBridges():
    return [
        voiceBridge[0]
        for voiceBridge in db.session.query(PreviousVoiceBridge.voiceBridge)
    ]


def delete_old_voiceBridges():
    db.session.query(PreviousVoiceBridge).filter(
        PreviousVoiceBridge.archived_at < datetime.now() - timedelta(days=365)
    ).delete()


def get_quick_meeting_from_user_and_random_string(user, random_string=None):
    if random_string is None:
        random_string = get_random_alphanumeric_string(8)

    meeting = Meeting(
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        user=user,
        name=current_app.config["QUICK_MEETING_DEFAULT_NAME"],
        moderatorPW=f"{user.hash}-{random_string}",
        attendeePW=f"{random_string}-{random_string}",
        moderatorOnlyMessage=current_app.config[
            "QUICK_MEETING_MODERATOR_WELCOME_MESSAGE"
        ],
        logoutUrl=(
            current_app.config["QUICK_MEETING_LOGOUT_URL"]
            or url_for("public.index", _external=True)
        ),
    )
    meeting.fake_id = random_string
    return meeting


def get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id):
    if meeting_fake_id.isdigit():
        try:
            meeting = db.session.get(Meeting, meeting_fake_id)
        except:
            try:
                user = db.session.get(User, user_id)
                meeting = get_quick_meeting_from_user_and_random_string(
                    user, random_string=meeting_fake_id
                )
            except:
                meeting = None
    else:
        try:
            user = db.session.get(User, user_id)
            meeting = get_quick_meeting_from_user_and_random_string(
                user, random_string=meeting_fake_id
            )
        except:
            meeting = None

    return meeting


def get_mail_meeting(random_string=None):
    # only used for mail meeting
    if random_string is None:
        random_string = get_random_alphanumeric_string(8)

    meeting = Meeting(
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        name=current_app.config["QUICK_MEETING_DEFAULT_NAME"],
        moderatorPW=f"{random_string}-{random_string}",  # it is only usefull for bbb
        moderatorOnlyMessage=current_app.config["MAIL_MODERATOR_WELCOME_MESSAGE"],
        logoutUrl=(
            current_app.config["QUICK_MEETING_LOGOUT_URL"]
            or url_for("public.index", _external=True)
        ),
    )
    meeting.fake_id = random_string
    return meeting


def pin_generation(forbidden_pins=None, clean_db=True):
    if clean_db:
        delete_old_voiceBridges()
    forbidden_pins = get_forbidden_pins() if forbidden_pins is None else forbidden_pins
    return create_unique_pin(forbidden_pins=forbidden_pins)


def get_forbidden_pins(edited_meeting_id=None):
    previous_pins = get_all_previous_voiceBridges()

    existing_meeting_voiceBridges = db.session.query(Meeting.voiceBridge)

    if edited_meeting_id:
        existing_meeting_voiceBridges = existing_meeting_voiceBridges.filter(
            Meeting.id != edited_meeting_id
        )

    return [
        voiceBridge[0] for voiceBridge in existing_meeting_voiceBridges
    ] + previous_pins


def create_unique_pin(forbidden_pins, pin=None):
    pin = random.randint(100000000, 999999999) if not pin else pin
    if str(pin) in forbidden_pins:
        pin += 1
        pin = 100000000 if pin > 999999999 else pin
        return create_unique_pin(forbidden_pins, pin)
    else:
        return str(pin)


def pin_is_unique_validator(form, field):
    if field.data in get_forbidden_pins(form.id.data):
        raise ValidationError("Ce code PIN est déjà utilisé")


def create_and_save_shadow_meeting(user):
    random_string = get_random_alphanumeric_string(8)
    meeting = Meeting(
        name=f"{current_app.config['WORDING_THE_MEETING']} de {user.fullname}",
        welcome=f"Bienvenue dans {current_app.config['WORDING_THE_MEETING']} de {user.fullname}",
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        maxParticipants=350,
        logoutUrl=current_app.config["MEETING_LOGOUT_URL"],
        moderatorOnlyMessage=str(_("Bienvenue aux modérateurs")),
        record=False,
        autoStartRecording=False,
        allowStartStopRecording=False,
        lockSettingsDisableMic=False,
        lockSettingsDisablePrivateChat=False,
        lockSettingsDisablePublicChat=False,
        lockSettingsDisableNote=False,
        lockSettingsDisableCam=False,
        allowModsToUnmuteUsers=False,
        webcamsOnlyForModerator=False,
        muteOnStart=True,
        guestPolicy=False,
        logo=None,
        is_shadow=True,
        user=user,
        attendeePW=f"{random_string}-{random_string}",
        moderatorPW=f"{user.hash}-{random_string}",
        voiceBridge=pin_generation(),
        visio_code=unique_visio_code_generation(),
    )
    meeting.save()
    return meeting


def get_or_create_shadow_meeting(user):
    shadow_meetings = [
        shadow_meeting
        for shadow_meeting in db.session.query(Meeting).filter(
            Meeting.is_shadow,
            Meeting.user_id == user.id,
        )
    ]
    if len(shadow_meetings) > 1:
        for shadow_meeting in shadow_meetings:
            if shadow_meeting is not shadow_meetings[0]:
                save_voiceBridge_and_delete_meeting(shadow_meeting)
    meeting = (
        create_and_save_shadow_meeting(user)
        if not shadow_meetings
        else shadow_meetings[0]
    )
    return meeting


def save_voiceBridge_and_delete_meeting(meeting):
    previous_voiceBridge = PreviousVoiceBridge()
    previous_voiceBridge.voiceBridge = meeting.voiceBridge
    previous_voiceBridge.save()
    db.session.delete(meeting)
    db.session.commit()


def delete_all_old_shadow_meetings():
    old_shadow_meetings = [
        shadow_meeting
        for shadow_meeting in db.session.query(Meeting).filter(
            Meeting.last_connection_utc_datetime < datetime.now() - timedelta(days=365),
            Meeting.is_shadow,
        )
    ]

    for shadow_meeting in old_shadow_meetings:
        save_voiceBridge_and_delete_meeting(shadow_meeting)


def unique_visio_code_generation(forbidden_visio_code=None):
    forbidden_visio_code = (
        get_all_visio_codes() if forbidden_visio_code is None else forbidden_visio_code
    )
    new_visio_code = create_unique_pin(forbidden_visio_code)
    if new_visio_code not in forbidden_visio_code and new_visio_code.isdigit():
        return new_visio_code.upper()
    return unique_visio_code_generation(forbidden_visio_code=forbidden_visio_code)


def get_all_visio_codes():
    existing_visio_code = db.session.query(Meeting.visio_code)
    return [visio_code[0] for visio_code in existing_visio_code]


def get_meeting_by_visio_code(visio_code):
    return (
        db.session.query(Meeting).filter(Meeting.visio_code == visio_code).one_or_none()
    )
