from datetime import timedelta

from flask import current_app
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import FloatField
from wtforms import Form
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators

from b3desk.models.meetings import DEFAULT_MAX_PARTICIPANTS
from b3desk.models.meetings import MODERATOR_ONLY_MESSAGE_MAXLENGTH
from b3desk.models.meetings import PIN_LENGTH
from b3desk.models.meetings import pin_generation
from b3desk.models.meetings import pin_is_unique_validator

MAX_URL_LENGTH = 255
MAX_LOGOUTURL_LENGTH = 250
MAX_MEETING_NAME_LENGTH = 150
DEFAULT_MEETING_DURATION = timedelta(hours=4, minutes=40)
MAX_MEETING_DURATION = timedelta(minutes=999)


class JoinMeetingForm(FlaskForm):
    fullname = StringField()
    meeting_fake_id = StringField()
    hash_ = StringField()
    fullname_suffix = StringField()
    seconds_before_refresh = FloatField()
    quick_meeting = BooleanField()


class ShowMeetingForm(Form):
    meeting_id = IntegerField()


class MeetingFilesForm(FlaskForm):
    url = TextAreaField(
        label=_("Lien web du fichier à ajouter"),
        description=_("Le lien web à entrer doit permettre de télécharger un fichier"),
        render_kw={"rows": 1, "placeholder": "https://exemple.com/image.jpg"},
        validators=[
            validators.length(max=MAX_URL_LENGTH, message=_("Le texte est trop long"))
        ],
    )
    guestPolicy = BooleanField(
        label=_("Salle d'attente"),
        description=_(
            "Placer les participants dans une salle d'attente lorsqu'ils rejoignent la réunion. L'organisateur ou le modérateur devra les accepter individuellement."
        ),
        default=False,
    )


class MeetingForm(FlaskForm):
    id = IntegerField()
    name = StringField(
        label=_(
            "Nom de la réunion",
        ),
        description=_(
            "Vous ne pourrez plus changer ce titre une fois la salle créée. Ce nom est visible des participants",
        ),
        default=_(
            "Ma réunion",
        ),
        validators=[
            validators.DataRequired(),
            validators.length(max=MAX_MEETING_NAME_LENGTH),
        ],
    )
    welcome = TextAreaField(
        label=_("Texte de bienvenue"),
        description=_(
            "Ce texte apparait comme message de bienvenue sur le tchat public. 150 caractères max."
        ),
        default=_(
            "Bienvenue dans cette réunion %(meeting_name)s.",
            meeting_name="<u><strong> %%CONFNAME%% </strong></u>",
        ),
        render_kw={"rows": 3},
        validators=[validators.length(max=MODERATOR_ONLY_MESSAGE_MAXLENGTH)],
    )
    maxParticipants = IntegerField(
        label=_("Nombre maximal de participants"),
        description=_("Limitez vos salons à 350 personnes pour plus de confort."),
        default=DEFAULT_MAX_PARTICIPANTS,
    )
    duration = IntegerField(
        label=_("Durée maximale (minutes)"),
        description=_(
            "A l'issue de cette durée la réunion stoppe automatiquement. 1h = 60, 2h = 120, 3h = 180, 4h = 240.",
        ),
        default=int(DEFAULT_MEETING_DURATION.total_seconds() // 60),
        validators=[
            validators.NumberRange(
                min=1, max=int(MAX_MEETING_DURATION.total_seconds() // 60)
            )
        ],
    )
    guestPolicy = BooleanField(
        label=_("Salle d'attente"),
        description=_(
            "Placer les participants dans une salle d'attente lorsqu'ils rejoignent la réunion. L'organisateur ou le modérateur devra les accepter individuellement.",
        ),
        default=False,
    )
    webcamsOnlyForModerator = BooleanField(
        label=_("Caméras visibles par les modérateurs uniquement"),
        description=_(
            "Seuls vous et les modérateurs pouvez voir les caméras des autres participants quand cette option est activée."
        ),
        default=False,
    )
    muteOnStart = BooleanField(
        label=_("Participants muets à leur arrivée"),
        description=_(
            "Vous pouvez choisir de faire arriver les participants dans la salle avec leur micro fermé, pour un démarrage de réunion plus calme."
        ),
        default=True,
    )
    lockSettingsDisableCam = BooleanField(
        label=_("Caméras des participants"),
        description=_(
            "Vous pouvez autoriser ou interdire l'ouverture de la caméra des participants."
        ),
        filters=[lambda x: not x],
        default=False,
    )
    lockSettingsDisableMic = BooleanField(
        label=_("Micros des participants"),
        description=_(
            "Vous pouvez autoriser ou interdire l'ouverture du microphone des participants."
        ),
        filters=[lambda x: not x],
        default=False,
    )
    lockSettingsDisablePrivateChat = BooleanField(
        label=_("Discussions privées"),
        filters=[lambda x: not x],
        default=False,
    )
    lockSettingsDisablePublicChat = BooleanField(
        label=_("Discussion publique (tchat)"),
        filters=[lambda x: not x],
        default=False,
    )
    lockSettingsDisableNote = BooleanField(
        label=_("Prise de note collaborative"),
        filters=[lambda x: not x],
        default=False,
    )
    moderatorOnlyMessage = TextAreaField(
        label=_("Message à l'attention des modérateurs"),
        description=_("150 caractères max"),
        default=_("Bienvenue aux modérateurs"),
        validators=[
            validators.length(
                max=MODERATOR_ONLY_MESSAGE_MAXLENGTH,
                message=_("Le message est trop long"),
            )
        ],
        render_kw={"rows": 3},
    )
    logoutUrl = StringField(
        label=_(
            "Url de redirection après la réunion",
        ),
        default=current_app.config["MEETING_LOGOUT_URL"],
        validators=[validators.length(max=MAX_LOGOUTURL_LENGTH)],
        render_kw={"placeholder": current_app.config["MEETING_LOGOUT_URL"]},
    )
    moderatorPW = StringField(
        label=_("Renouveler le lien modérateur"),
        description=_(
            "Ce code vous permet si vous le changez de bloquer les anciens liens."
        ),
        default="Pa55W0rd1",
        render_kw={"readonly": True},
        validators=[validators.DataRequired()],
    )
    attendeePW = StringField(
        label=_("Renouveler le lien participants"),
        description=_(
            "Ce code vous permet si vous le changez de bloquer les anciens liens."
        ),
        default="Pa55W0rd2",
        render_kw={"readonly": True},
        validators=[validators.DataRequired()],
    )
    voiceBridge = StringField(
        label=_("PIN"),
        description=_(
            "Code PIN pour rejoindre la réunion par téléphone (9 chiffres)",
        ),
        default=lambda: pin_generation(),
        validators=[
            validators.DataRequired(),
            validators.length(
                min=PIN_LENGTH, max=PIN_LENGTH, message=_("Entez un PIN de 9 chiffres")
            ),
            validators.Regexp(
                regex=f"[0-9]{{{PIN_LENGTH}}}",
                message=_("Le code PIN est composé de chiffres uniquement"),
            ),
            validators.Regexp(
                regex="^[1-9]", message=_("Le premier chiffre doit être différent de 0")
            ),
            pin_is_unique_validator,
        ],
    )
    visio_code = StringField(
        label=_("Code de connexion"),
        description=_(
            "Code de connexion pour rejoindre la réunion %(sip)s",
            sip=_("(utilisé dans le lien SIP)")
            if current_app.config["ENABLE_SIP"]
            else "",
        ),
        render_kw={"readonly": True},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logoutUrl.default = current_app.config["MEETING_LOGOUT_URL"]


class MeetingWithRecordForm(MeetingForm):
    allowStartStopRecording = BooleanField(
        label=_("Enregistrement manuel"),
        description=_(
            "Vous pouvez lancer ou arrêter à tout moment l'enregistrement de la salle."
        ),
        default=True,
    )
    autoStartRecording = BooleanField(
        label=_("Enregistrement automatique"),
        description=_(
            "L'enregistrement démarre automatiquement à l'ouverture de la salle et s'arrête à sa fermeture."
        ),
        default=False,
    )


class RecordingForm(FlaskForm):
    name = StringField(
        validators=[validators.DataRequired()], label=_("Nom de l'enregistrement")
    )


class EndMeetingForm(FlaskForm):
    meeting_id = HiddenField()
