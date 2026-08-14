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
import random
import uuid
from datetime import date
from datetime import datetime
from datetime import timedelta
from enum import IntEnum

from flask import current_app
from flask_babel import lazy_gettext as _
from itsdangerous import Signer
from itsdangerous import URLSafeSerializer
from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import UniqueConstraint
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from wtforms import ValidationError

from b3desk.utils import get_random_alphanumeric_string
from b3desk.utils import secret_key
from b3desk.utils.mailing import DELAY_FOR_FIRST_EMAIL
from b3desk.utils.mailing import DELAY_FOR_SECOND_EMAIL
from b3desk.utils.mailing import DELAY_FOR_THIRD_EMAIL

from . import db
from .roles import Role
from .users import User


class AccessLevel(IntEnum):
    NONE = 0
    DELEGATE = 1


class MeetingAccess(db.Model):
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meeting.id"), primary_key=True)
    level: Mapped[int]

    user: Mapped[User] = relationship(back_populates="user_meeting_access")
    meeting: Mapped[Meeting] = relationship(back_populates="meeting_access")


favorite_table = db.Table(
    "favorite",
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("meeting_id", ForeignKey("meeting.id"), primary_key=True),
)

MODERATOR_ONLY_MESSAGE_MAXLENGTH = 150
DEFAULT_MAX_PARTICIPANTS = 350
PIN_LENGTH = 9
MIN_PIN = 100000000
MAX_PIN = 999999999
MAX_GENERATION_ATTEMPTS = 20
TITLE_TRUNCATE_THRESHOLD = 70
TITLE_TRUNCATE_LENGTH = 30
DATA_RETENTION = timedelta(days=365)
PASSWORD_HASH_LENGTH = 16


def get_meeting_file_hash(*args):
    serializer = URLSafeSerializer(
        current_app.config["SECRET_KEY"], salt="meeting-file"
    )
    return serializer.dumps(args)


class BaseMeetingFiles:
    def __init__(
        self, id=None, title=None, nc_path=None, meeting_id=None, owner=None, **kwargs
    ):
        self.id = id
        self.title = title
        self.nc_path = nc_path
        self.meeting_id = meeting_id
        self.owner = owner
        super().__init__(**kwargs)


class MeetingFiles(BaseMeetingFiles, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(Unicode(4096))
    url: Mapped[str | None] = mapped_column(Unicode(4096))
    nc_path: Mapped[str | None] = mapped_column(Unicode(4096))
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meeting.id"))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"))
    is_downloadable: Mapped[bool | None] = mapped_column(default=False)
    created_at: Mapped[date | None] = mapped_column(Date)

    meeting: Mapped[Meeting] = relationship(back_populates="files")
    owner: Mapped[User | None] = relationship(foreign_keys=[owner_id])

    @property
    def short_title(self):
        """Return a truncated version of the title if it exceeds the threshold."""
        return (
            self.title
            if len(self.title) < TITLE_TRUNCATE_THRESHOLD
            else f"{self.title[:TITLE_TRUNCATE_LENGTH]}...{self.title[-TITLE_TRUNCATE_LENGTH:]}"
        )


class BaseMeetingSecretKey:
    def __init__(self, id=None, meeting_id=None, role=None, **kwargs):
        self.id = id
        self.meeting_id = meeting_id
        self.role = role
        super().__init__(**kwargs)


class MeetingSecretKey(BaseMeetingSecretKey, db.Model):
    __table_args__ = (UniqueConstraint("meeting_id", "role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meeting.id", ondelete="CASCADE")
    )
    role: Mapped[str | None] = mapped_column(String(255))
    secret_key: Mapped[str] = mapped_column(
        String(255), unique=True, default=lambda: str(uuid.uuid7())
    )
    legacy_secret_keys: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )  # old sha1-hash schemes
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    meeting: Mapped[Meeting] = relationship(back_populates="secret_keys")


class Meeting(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    bbb_meeting_id: Mapped[str] = mapped_column(
        String(255), unique=True, default=lambda: str(uuid.uuid7())
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    owner: Mapped[User] = relationship(back_populates="meetings")

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )
    files: Mapped[list[MeetingFiles]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    secret_keys: Mapped[list[MeetingSecretKey]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    meeting_access: Mapped[list[MeetingAccess]] = relationship(back_populates="meeting")
    last_connection_utc_datetime: Mapped[datetime | None]
    is_shadow: Mapped[bool | None] = mapped_column(default=False)
    visio_code: Mapped[str] = mapped_column(Unicode(50), unique=True)

    # BBB params
    name: Mapped[str | None] = mapped_column(Unicode(150))
    attendeePW: Mapped[str | None] = mapped_column(
        StringEncryptedType(Unicode(50), secret_key())
    )
    moderatorPW: Mapped[str | None] = mapped_column(
        StringEncryptedType(Unicode(50), secret_key())
    )
    welcome: Mapped[str | None] = mapped_column(UnicodeText())
    dialNumber: Mapped[str | None] = mapped_column(Unicode(50))
    voiceBridge: Mapped[str] = mapped_column(Unicode(50), unique=True)
    maxParticipants: Mapped[int | None]
    logoutUrl: Mapped[str | None] = mapped_column(Unicode(250))
    record: Mapped[bool | None] = mapped_column(default=True)
    duration: Mapped[int | None]
    moderatorOnlyMessage: Mapped[str | None] = mapped_column(
        Unicode(MODERATOR_ONLY_MESSAGE_MAXLENGTH)
    )
    autoStartRecording: Mapped[bool | None] = mapped_column(default=True)
    allowStartStopRecording: Mapped[bool | None] = mapped_column(default=True)
    webcamsOnlyForModerator: Mapped[bool | None] = mapped_column(default=True)
    muteOnStart: Mapped[bool | None] = mapped_column(default=True)
    lockSettingsDisableCam: Mapped[bool | None] = mapped_column(default=True)
    lockSettingsDisableMic: Mapped[bool | None] = mapped_column(default=True)
    allowModsToUnmuteUsers: Mapped[bool | None] = mapped_column(default=False)
    lockSettingsDisablePrivateChat: Mapped[bool | None] = mapped_column(default=True)
    lockSettingsDisablePublicChat: Mapped[bool | None] = mapped_column(default=True)
    lockSettingsDisableNote: Mapped[bool | None] = mapped_column(default=True)
    ai_summary: Mapped[bool] = mapped_column(default=False)
    guestPolicy: Mapped[bool | None] = mapped_column(default=True)
    logo: Mapped[str | None] = mapped_column(Unicode(200))

    favorite_of: Mapped[list[User]] = relationship(
        secondary=favorite_table, back_populates="favorites"
    )

    _bbb = None

    quick = False

    @property
    def bbb(self):
        """Return the BBB API interface for this meeting."""
        from .bbb import BBB

        if not self._bbb:
            self._bbb = BBB(self.bbb_meeting_id)
        return self._bbb

    @property
    def ai_summary_enabled(self):
        """Whether the AI summary recording format is expected for this meeting."""
        return bool(self.ai_summary) and self.owner.can_use_ai_summary

    @property
    def get_all_delegates(self):
        return db.session.scalars(
            db.select(User)
            .join(MeetingAccess)
            .where(
                MeetingAccess.meeting_id == self.id,
                MeetingAccess.level == AccessLevel.DELEGATE,
            )
        ).all()

    def url_for_role(self, role):
        from b3desk.join import create_signin_url

        meeting_secret_key = next(
            (
                secret_key
                for secret_key in self.secret_keys
                if secret_key.role == role.name
            ),
            None,
        )
        if not meeting_secret_key:
            return None
        return create_signin_url(self, role, meeting_secret_key.secret_key)

    @property
    def moderator_url(self):
        return self.url_for_role(Role.moderator)

    @property
    def attendee_url(self):
        return self.url_for_role(Role.attendee)

    @property
    def authenticated_url(self):
        return self.url_for_role(Role.authenticated)

    def create_secret_keys(self):
        for role in Role:
            db.session.add(MeetingSecretKey(meeting_id=self.id, role=role.name))

    def renew_secret_key(self, role):
        """Regenerate a role's secret key, invalidating its previous signin link."""
        meeting_secret_key = db.session.scalars(
            db.select(MeetingSecretKey).where(
                MeetingSecretKey.meeting_id == self.id,
                MeetingSecretKey.role == role.name,
            )
        ).one()
        meeting_secret_key.secret_key = str(uuid.uuid7())
        meeting_secret_key.legacy_secret_keys = []


class PreviousVoiceBridge(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    voiceBridge: Mapped[str] = mapped_column(Unicode(50), unique=True)
    archived_at: Mapped[datetime] = mapped_column(default=datetime.now)


def get_all_previous_voiceBridges():
    """Retrieve all archived voice bridge codes."""
    return list(db.session.scalars(db.select(PreviousVoiceBridge.voiceBridge)))


def delete_old_voiceBridges():
    """Delete archived voice bridges older than one year."""
    db.session.execute(
        db.delete(PreviousVoiceBridge).where(
            PreviousVoiceBridge.archived_at < datetime.now() - DATA_RETENTION
        )
    )


def get_deterministic_password(meeting_id, role):
    """Generate a deterministic password based on meeting ID and role."""
    signer = Signer(current_app.config["SECRET_KEY"])
    return (
        signer.sign(f"{meeting_id}-{role}")
        .decode()
        .split(".")[-1][:PASSWORD_HASH_LENGTH]
    )


def get_quick_meeting_bbb_meeting_id(meeting_id):
    """Return the BBB room identifier of a quick meeting."""
    # Quick meetings used to be identified by a random string, and their BBB
    # room by the 'meeting-vanish-{id}--' form that the signin link hashes were
    # built upon. Rebuilding that form keeps the rooms and the links emitted
    # before the UUID identifiers reachable, until they all expire.
    # To be removed in version 1.8.
    try:
        uuid.UUID(meeting_id)
    except ValueError:
        return f"meeting-vanish-{meeting_id}--"
    return meeting_id


def get_quick_meeting_from_meeting_id(meeting_id=None):
    """Build a non-persisted quick meeting identified by meeting_id (or a fresh random one)."""
    meeting_id = meeting_id or str(uuid.uuid7())
    meeting = Meeting(
        id=meeting_id,
        bbb_meeting_id=get_quick_meeting_bbb_meeting_id(meeting_id),
        attendeePW=get_deterministic_password(meeting_id, "attendee"),
    )
    meeting.quick = True
    return meeting


def get_meeting_from_meeting_id(meeting_id):
    """Retrieve a persisted meeting by id, or build a quick (non-persisted) one if none exists."""
    if meeting_id.isdigit():
        return db.session.get(Meeting, meeting_id)
    return get_quick_meeting_from_meeting_id(meeting_id)


def get_meeting_from_bbb_meeting_id(bbb_meeting_id):
    """Retrieve a persisted Meeting from a BBB-side identifier (new UUID or legacy 'meeting-persistent-...' form)."""
    return db.session.scalars(
        db.select(Meeting).where(Meeting.bbb_meeting_id == bbb_meeting_id)
    ).one_or_none()


def generate_random_pin():
    """Generate a random 9-digit PIN."""
    return str(random.randint(MIN_PIN, MAX_PIN))


def pin_exists(pin):
    """Check if a PIN already exists in meetings or archived voice bridges."""
    return db.session.scalar(
        db.select(
            or_(
                db.select(Meeting).where(Meeting.voiceBridge == pin).exists(),
                db.select(PreviousVoiceBridge)
                .where(PreviousVoiceBridge.voiceBridge == pin)
                .exists(),
            )
        )
    )


def pin_generation():
    """Generate a unique PIN for voice bridge."""
    delete_old_voiceBridges()
    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        pin = generate_random_pin()
        if not pin_exists(pin):
            return pin
    raise RuntimeError(
        "Could not generate unique PIN after maximum attempts"
    )  # pragma: no cover


def get_forbidden_pins(edited_meeting_id=None):
    """Retrieve all voice bridge PINs that are already in use or archived."""
    previous_pins = get_all_previous_voiceBridges()

    existing_meeting_voiceBridges = db.select(Meeting.voiceBridge)

    if edited_meeting_id:
        existing_meeting_voiceBridges = existing_meeting_voiceBridges.where(
            Meeting.id != edited_meeting_id
        )

    return list(db.session.scalars(existing_meeting_voiceBridges)) + previous_pins


def pin_is_unique_validator(form, field):
    """Validate that a PIN is unique and not already in use."""
    pin = field.data
    # Check if PIN exists in archived voice bridges
    archived_exists = db.session.scalar(
        db.select(
            db.select(PreviousVoiceBridge)
            .where(PreviousVoiceBridge.voiceBridge == pin)
            .exists()
        )
    )
    if archived_exists:
        raise ValidationError(_("Ce code PIN est déjà utilisé"))

    # Check if PIN exists in other meetings (excluding current meeting if editing)
    query = db.select(Meeting).where(Meeting.voiceBridge == pin)
    if form.id.data:
        query = query.where(Meeting.id != form.id.data)
    if db.session.scalar(db.select(query.exists())):
        raise ValidationError(_("Ce code PIN est déjà utilisé"))


def create_and_save_shadow_meeting(user):
    """Create and save a new shadow meeting for a user."""
    random_string = get_random_alphanumeric_string(8)
    meeting = Meeting(
        name=str(_("la réunion de %(fullname)s", fullname=user.fullname)),
        welcome=str(
            _("Bienvenue dans la réunion de %(fullname)s", fullname=user.fullname)
        ),
        duration=current_app.config["DEFAULT_MEETING_DURATION"],
        maxParticipants=DEFAULT_MAX_PARTICIPANTS,
        logoutUrl=current_app.config["MEETING_LOGOUT_URL"],
        moderatorOnlyMessage=str(_("Bienvenue aux modérateurs")),
        record=False,
        autoStartRecording=False,
        ai_summary=False,
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
        owner=user,
        attendeePW=f"{random_string}-{random_string}",
        moderatorPW=f"{user.hash}-{random_string}",
    )
    db.session.add(meeting)
    assign_unique_codes(meeting)
    meeting.create_secret_keys()
    db.session.commit()
    return meeting


def get_or_create_shadow_meeting(user):
    """Retrieve the user's shadow meeting or create one if it doesn't exist."""
    shadow_meetings = db.session.scalars(
        db.select(Meeting).where(
            Meeting.is_shadow,
            Meeting.owner_id == user.id,
        )
    ).all()
    if len(shadow_meetings) > 1:
        for shadow_meeting in shadow_meetings:
            if shadow_meeting is not shadow_meetings[0]:
                clean_db_and_delete_meeting(shadow_meeting)
    return (
        create_and_save_shadow_meeting(user)
        if not shadow_meetings
        else shadow_meetings[0]
    )


def clean_db_and_delete_meeting(meeting, celery_cron=False):
    if celery_cron:
        for delegate in meeting.get_all_delegates:
            remove_delegate_from_db(meeting, delegate)
    if meeting.get_all_delegates:
        return False, None

    if not meeting.is_shadow:
        from .bbb import BBB

        data = BBB(meeting.bbb_meeting_id).delete_all_recordings()
        if data and not BBB.success(data):
            return False, data

    previous_voiceBridge = PreviousVoiceBridge()
    previous_voiceBridge.voiceBridge = meeting.voiceBridge
    db.session.add(previous_voiceBridge)
    db.session.delete(meeting)
    db.session.commit()

    return True, None


def visio_code_exists(code):
    """Check if a visio code already exists."""
    return db.session.scalar(
        db.select(db.select(Meeting).where(Meeting.visio_code == code).exists())
    )


def unique_visio_code_generation():
    """Generate a unique visio code not already in use (LBYL for endpoint)."""
    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        code = generate_random_pin()
        if not visio_code_exists(code):
            return code
    raise RuntimeError(
        "Could not generate unique visio code after maximum attempts"
    )  # pragma: no cover


def assign_unique_visio_code(meeting):
    """Assign a unique visio code to a meeting (EAFP with retry on collision)."""
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        meeting.visio_code = generate_random_pin()
        try:
            with db.session.begin_nested():
                db.session.flush()
            return
        except IntegrityError:  # pragma: no cover
            if attempt == MAX_GENERATION_ATTEMPTS - 1:
                raise


def assign_unique_voice_bridge(meeting):
    """Assign a unique voice bridge PIN to a meeting (EAFP with retry on collision)."""
    with db.session.no_autoflush:
        delete_old_voiceBridges()
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        meeting.voiceBridge = generate_random_pin()
        try:
            with db.session.begin_nested():
                db.session.flush()
            return
        except IntegrityError:  # pragma: no cover
            if attempt == MAX_GENERATION_ATTEMPTS - 1:
                raise


def assign_unique_codes(meeting):
    """Assign unique visio_code and voiceBridge to a new meeting (both before flush)."""
    with db.session.no_autoflush:
        delete_old_voiceBridges()
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        meeting.visio_code = generate_random_pin()
        meeting.voiceBridge = generate_random_pin()
        try:
            with db.session.begin_nested():
                db.session.flush()
            return
        except IntegrityError:  # pragma: no cover
            if attempt == MAX_GENERATION_ATTEMPTS - 1:
                raise


def get_meeting_by_visio_code(visio_code):
    """Retrieve a meeting by its visio code."""
    return db.session.scalars(
        db.select(Meeting).where(Meeting.visio_code == visio_code)
    ).one_or_none()


def remove_delegate_from_db(meeting, delegate):
    access = db.session.scalars(
        db.select(MeetingAccess).where(
            MeetingAccess.user_id == delegate.id,
            MeetingAccess.meeting_id == meeting.id,
        )
    ).one()
    db.session.delete(access)
    db.session.commit()


def get_inactive_meetings_to_delete():
    cutoff = datetime.now() - timedelta(
        days=current_app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
    )
    return db.session.scalars(
        db.select(Meeting).where(
            or_(
                Meeting.last_connection_utc_datetime < cutoff,
                (Meeting.last_connection_utc_datetime.is_(None))
                & (Meeting.created_at < cutoff),
            )
        )
    ).all()


def get_inactive_meetings_to_inform():
    today = datetime.now().date()
    inactivity_period = timedelta(
        days=current_app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
    )
    meetings = []
    for delay in (DELAY_FOR_FIRST_EMAIL, DELAY_FOR_SECOND_EMAIL, DELAY_FOR_THIRD_EMAIL):
        target_date = today + timedelta(days=delay) - inactivity_period
        day_start = datetime(target_date.year, target_date.month, target_date.day)
        day_end = day_start + timedelta(days=1)
        matching_meetings = db.session.scalars(
            db.select(Meeting).where(
                or_(
                    (Meeting.last_connection_utc_datetime >= day_start)
                    & (Meeting.last_connection_utc_datetime < day_end),
                    (Meeting.last_connection_utc_datetime.is_(None))
                    & (Meeting.created_at >= day_start)
                    & (Meeting.created_at < day_end),
                )
            )
        ).all()
        meetings += [(meeting, delay) for meeting in matching_meetings]
    return meetings
