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


def get_meeting_file_hash(meeting_file_id, isexternal):
    return hashlib.sha1(
        f"{current_app.config['SECRET_KEY']}-{1 if isexternal else 0}-{meeting_file_id}-{current_app.config['SECRET_KEY']}".encode()
    ).hexdigest()


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
        """Return a truncated version of the title if it exceeds 70 characters."""
        return (
            self.title
            if len(self.title) < 70
            else f"{self.title[:30]}...{self.title[-30:]}"
        )

    def update(self):
        """Commit changes to the database."""
        db.session.commit()

    def save(self):
        """Save the meeting file to the database."""
        db.session.add(self)
        db.session.commit()


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")

    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    is_favorite = db.Column(db.Boolean, unique=False, default=False)
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

    _bbb = None

    @property
    def bbb(self):
        """Return the BBB API interface for this meeting."""
        from .bbb import BBB

        if not self._bbb:
            self._bbb = BBB(self)
        return self._bbb

    @property
    def default_file(self):
        """Return the default file for this meeting, if any."""
        for mfile in self.files:
            if mfile.is_default:
                return mfile
        return None

    @property
    def non_default_files(self):
        """Return all non-default files for this meeting."""
        return [
            meeting_file for meeting_file in self.files if not meeting_file.is_default
        ]

    @property
    def meetingID(self):
        """Return the unique BBB meeting identifier."""
        if self.id is not None:
            fid = f"meeting-persistent-{self.id}"
        else:
            fid = f"meeting-vanish-{self.fake_id}"
        return "{}--{}".format(fid, self.user.hash if self.user else "")

    @property
    def fake_id(self):
        """Return the meeting ID or temporary fake ID for quick meetings."""
        if self.id is not None:
            return self.id
        else:
            try:
                return self._fake_id
            except:
                return None

    @fake_id.setter
    def fake_id(self, fake_value):
        """Set the temporary fake ID for quick meetings."""
        self._fake_id = fake_value

    @fake_id.deleter
    def fake_id(self):
        """Delete the temporary fake ID."""
        del self._fake_id

    def get_hash(self, role: Role, hash_from_string=False):
        """Generate a hash for meeting access verification based on role."""
        s = f"{self.meetingID}|{self.attendeePW}|{self.name}|{role.name if hash_from_string else role}"
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    def is_running(self):
        """Check if the BBB meeting is currently running."""
        data = self.bbb.is_meeting_running()
        return data and data["returncode"] == "SUCCESS" and data["running"] == "true"

    def create_bbb(self) -> bool:
        """Create the BBB meeting room and return the result."""
        if self.is_running():
            return False

        current_app.logger.info("Request BBB room creation %s %s", self.name, self.id)
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

        return result.get("returncode", "") == "SUCCESS"

    def save(self):
        """Save the meeting to the database."""
        db.session.add(self)
        db.session.commit()

    def delete_recordings(self, recording_ids):
        """Delete the specified recordings from BBB."""
        return self.bbb.delete_recordings(recording_ids)

    def delete_all_recordings(self):
        """Delete all recordings for this meeting."""
        recordings = self.get_recordings()
        if not recordings:
            return {}
        recording_ids = ",".join(
            [recording.get("recordID", "") for recording in recordings]
        )
        return self.delete_recordings(recording_ids)

    def get_recordings(self):
        """Retrieve all recordings for this meeting from BBB."""
        return self.bbb.get_recordings()

    def update_recording_name(self, recording_id, name):
        """Update the name of a recording in BBB."""
        return self.bbb.update_recordings(
            recording_ids=[recording_id], metadata={"name": name}
        )

    def get_join_url(
        self,
        meeting_role: Role,
        fullname,
        fullname_suffix="",
        quick_meeting=False,
        seconds_before_refresh=None,
        waiting_room=True,
    ):
        """Return the URL of the BBB meeting URL if available, and the URL of the b3desk 'waiting_meeting' if it is not ready."""
        if waiting_room and not self.is_running():
            return url_for(
                "join.waiting_meeting",
                meeting_fake_id=self.fake_id,
                creator=self.user,
                h=self.get_hash(meeting_role),
                fullname=fullname,
                fullname_suffix=fullname_suffix,
                seconds_before_refresh=seconds_before_refresh,
                quick_meeting=quick_meeting,
            )

        if self.id:
            self.last_connection_utc_datetime = datetime.now()
            self.save()

        nickname = f"{fullname} - {fullname_suffix}" if fullname_suffix else fullname
        return self.bbb.prepare_request_to_join_bbb(meeting_role, nickname).url

    def get_signin_url(self, meeting_role: Role):
        """Generate the sign-in URL for a specific role."""
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
        """Generate a hash for mail-based sign-in with expiration."""
        s = f"{meeting_id}-{expiration_epoch}"
        return hashlib.sha256(
            s.encode("utf-8") + secret_key().encode("utf-8")
        ).hexdigest()

    def get_mail_signin_url(self):
        """Generate a time-limited sign-in URL for mail invitations."""
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
        """Determine the meeting role based on hash and user ID."""
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
        """End the BBB meeting."""
        data = self.bbb.end()
        return data and data["returncode"] == "SUCCESS"


class PreviousVoiceBridge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voiceBridge = db.Column(db.Unicode(50), unique=True, nullable=False)
    archived_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def save(self):
        """Save the archived voice bridge to the database."""
        db.session.add(self)
        db.session.commit()


def get_all_previous_voiceBridges():
    """Retrieve all archived voice bridge codes."""
    return [
        voiceBridge[0]
        for voiceBridge in db.session.query(PreviousVoiceBridge.voiceBridge)
    ]


def delete_old_voiceBridges():
    """Delete archived voice bridges older than one year."""
    db.session.query(PreviousVoiceBridge).filter(
        PreviousVoiceBridge.archived_at < datetime.now() - timedelta(days=365)
    ).delete()


def get_quick_meeting_from_user_and_fake_id(user, meeting_fake_id=None):
    """Create a quick meeting instance for a user with default settings."""
    if meeting_fake_id is None:
        meeting_fake_id = get_random_alphanumeric_string(8)

    meeting = Meeting(
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        user=user,
        name=current_app.config["QUICK_MEETING_DEFAULT_NAME"],
        moderatorPW=f"{user.hash}-{meeting_fake_id}",
        attendeePW=f"{meeting_fake_id}-{meeting_fake_id}",
        moderatorOnlyMessage=current_app.config[
            "QUICK_MEETING_MODERATOR_WELCOME_MESSAGE"
        ],
        logoutUrl=(
            current_app.config["QUICK_MEETING_LOGOUT_URL"]
            or url_for("public.index", _external=True)
        ),
    )
    meeting.fake_id = meeting_fake_id
    return meeting


def get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id):
    """Retrieve a meeting by ID or create a quick meeting if it doesn't exist."""
    if meeting_fake_id.isdigit():
        try:
            meeting = db.session.get(Meeting, meeting_fake_id)
        except:
            try:
                user = db.session.get(User, user_id)
                meeting = get_quick_meeting_from_user_and_fake_id(
                    user, meeting_fake_id=meeting_fake_id
                )
            except:
                meeting = None
    else:
        try:
            user = db.session.get(User, user_id)
            meeting = get_quick_meeting_from_user_and_fake_id(
                user, meeting_fake_id=meeting_fake_id
            )
        except:
            meeting = None

    return meeting


def get_mail_meeting(meeting_fake_id=None):
    """Create a mail-based meeting instance without a user account."""
    # only used for mail meeting
    if meeting_fake_id is None:
        meeting_fake_id = get_random_alphanumeric_string(8)

    meeting = Meeting(
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        name=current_app.config["QUICK_MEETING_DEFAULT_NAME"],
        moderatorPW=f"{meeting_fake_id}-{meeting_fake_id}",  # it is only usefull for bbb
        moderatorOnlyMessage=current_app.config["MAIL_MODERATOR_WELCOME_MESSAGE"],
        logoutUrl=(
            current_app.config["QUICK_MEETING_LOGOUT_URL"]
            or url_for("public.index", _external=True)
        ),
    )
    meeting.fake_id = meeting_fake_id
    return meeting


def pin_generation(forbidden_pins=None, clean_db=True):
    """Generate a unique PIN for voice bridge, avoiding forbidden pins."""
    if clean_db:
        delete_old_voiceBridges()
    forbidden_pins = get_forbidden_pins() if forbidden_pins is None else forbidden_pins
    return create_unique_pin(forbidden_pins=forbidden_pins)


def get_forbidden_pins(edited_meeting_id=None):
    """Retrieve all voice bridge PINs that are already in use or archived."""
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
    """Create a unique 9-digit PIN that is not in the forbidden list."""
    MIN_PIN = 100000000
    MAX_PIN = 999999999
    pin = random.randint(MIN_PIN, MAX_PIN) if not pin else pin
    if str(pin) in forbidden_pins:
        pin += 1
        pin = MIN_PIN if pin > MAX_PIN else pin
        return create_unique_pin(forbidden_pins, pin)
    else:
        return str(pin)


def pin_is_unique_validator(form, field):
    """Validate that a PIN is unique and not already in use."""
    if field.data in get_forbidden_pins(form.id.data):
        raise ValidationError("Ce code PIN est déjà utilisé")


def create_and_save_shadow_meeting(user):
    """Create and save a new shadow meeting for a user."""
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
    """Retrieve the user's shadow meeting or create one if it doesn't exist."""
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
    """Archive a meeting's voice bridge and delete the meeting from the database."""
    previous_voiceBridge = PreviousVoiceBridge()
    previous_voiceBridge.voiceBridge = meeting.voiceBridge
    previous_voiceBridge.save()
    db.session.delete(meeting)
    db.session.commit()


def delete_all_old_shadow_meetings():
    """Delete all shadow meetings not used in the past year."""
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
    """Generate a unique visio code not already in use."""
    forbidden_visio_code = (
        get_all_visio_codes() if forbidden_visio_code is None else forbidden_visio_code
    )
    new_visio_code = create_unique_pin(forbidden_visio_code)
    if new_visio_code not in forbidden_visio_code and new_visio_code.isdigit():
        return new_visio_code.upper()
    return unique_visio_code_generation(forbidden_visio_code=forbidden_visio_code)


def get_all_visio_codes():
    """Retrieve all existing visio codes from the database."""
    existing_visio_code = db.session.query(Meeting.visio_code)
    return [visio_code[0] for visio_code in existing_visio_code]


def get_meeting_by_visio_code(visio_code):
    """Retrieve a meeting by its visio code."""
    return (
        db.session.query(Meeting).filter(Meeting.visio_code == visio_code).one_or_none()
    )
