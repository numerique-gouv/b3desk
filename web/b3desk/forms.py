from datetime import timedelta

from flask import current_app
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import BooleanField
from wtforms import ButtonField
from wtforms import EmailField
from wtforms import FloatField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import SelectChoice
from wtforms import SelectField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import ValidationError
from wtforms import validators
from wtforms.widgets import HiddenInput

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
BARE_FIELD_TYPES = {"HiddenField", "CSRFTokenField", "SubmitField", "ButtonField"}


class B3DeskForm(FlaskForm):
    """Render every field through a Jinja template.

    Hidden fields and buttons render bare.
    """

    class Meta:
        field_template = "_field.html"
        field_class = ""

        def render_field(self, field, render_kw):
            render_kw = {**(field.render_kw or {}), **render_kw}
            if (
                field.type in BARE_FIELD_TYPES
                or isinstance(field.widget, HiddenInput)
                or render_kw.get("type") == "hidden"
            ):
                return field.widget(field, **render_kw)

            template = current_app.jinja_env.get_template(self.field_template)
            return Markup(template.render(field=field, render_kw=render_kw))


class ConfirmForm(B3DeskForm):
    """A CSRF token and a button, for forms that only trigger an action."""

    confirm = ButtonField()


class DeleteRecordingForm(ConfirmForm):
    recordID = HiddenField()


class AddGroupMembersForm(B3DeskForm):
    add_members = ButtonField(_("Ajouter les utilisateurs sélectionnés"))


class JoinMeetingForm(B3DeskForm):
    fullname = StringField(
        label=_("Votre nom"),
        description=_(
            "Vous pouvez également préciser votre service ou votre fonction."
        ),
        render_kw={"required": True},
    )
    meeting_id = HiddenField()
    secret_key = HiddenField()
    fullname_suffix = HiddenField()
    seconds_before_refresh = FloatField(widget=HiddenInput())
    join = ButtonField(_("Rejoindre"))


class ChunkUploadForm(FlaskForm):
    """Dropzone chunk metadata."""

    dzchunkindex = IntegerField(validators=[validators.InputRequired()])
    dzchunkbyteoffset = IntegerField(validators=[validators.InputRequired()])
    dztotalchunkcount = IntegerField(validators=[validators.InputRequired()])
    dztotalfilesize = IntegerField(validators=[validators.InputRequired()])


class MeetingFilesForm(FlaskForm):
    url = TextAreaField(
        label=_("Lien web du fichier à ajouter"),
        description=_("Le lien web à entrer doit permettre de télécharger un fichier"),
        render_kw={"rows": 1, "placeholder": "https://exemple.com/image.jpg"},
        validators=[
            validators.length(max=MAX_URL_LENGTH, message=_("Le texte est trop long"))
        ],
    )


class MeetingForm(B3DeskForm):
    class Meta:
        field_class = "fr-col-12 fr-py-2w"

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
        render_kw={"pattern": "[^\\x22]+"},
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
        render_kw={
            "placeholder": current_app.config["MEETING_LOGOUT_URL"],
            "pattern": "[^\\x22]+",
        },
    )
    moderatorPW = StringField(
        label=_("Renouveler le lien modérateur"),
        description=_(
            "Ce code vous permet si vous le changez de bloquer les anciens liens."
        ),
        default="Pa55W0rd1",
        render_kw={"readonly": True, "generate_button": True},
        validators=[validators.DataRequired()],
    )
    attendeePW = StringField(
        label=_("Renouveler le lien participants"),
        description=_(
            "Ce code vous permet si vous le changez de bloquer les anciens liens."
        ),
        default="Pa55W0rd2",
        render_kw={"readonly": True, "generate_button": True},
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
        render_kw={"readonly": True, "reset_visio_code_button": True},
    )
    save = ButtonField()

    showParticipantsOnLogin = BooleanField(
        label=_("Liste des participants visible"),
        default=True,
    )

    showPublicChatOnLogin = BooleanField(
        label=_("Chat affiché à l'ouverture"),
        default=True,
    )

    showPresentationOnJoin = BooleanField(
        label=_("Présentation affichée à l'ouverture"),
        default=True,
    )

    showSessionDetailsOnJoin = BooleanField(
        label=_("Informations affichées à l'ouverture"),
        default=False,
    )

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting
        if meeting is not None:
            self.name.render_kw = {**self.name.render_kw, "disabled": True}
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
    ai_summary = BooleanField(
        label=_("Génération de résumé (IA)"),
        description=_(
            "La génération de résumé est basée sur l'audio de l'enregistrement."
        ),
        default=True,
    )

    def validate_ai_summary(self, field):
        if field.data and not (
            self.allowStartStopRecording.data or self.autoStartRecording.data
        ):
            raise ValidationError(
                _(
                    "La génération de résumé nécessite d'activer l'enregistrement manuel ou automatique."
                )
            )


class RecordingForm(B3DeskForm):
    name = StringField(
        validators=[validators.DataRequired()], label=_("Nom de l'enregistrement")
    )
    rename = ButtonField(_("Renommer"))


class DelegationSearchForm(B3DeskForm):
    class Meta:
        field_template = "_search_field.html"

    search = EmailField(
        label=_("Ajout d'utilisateur"),
        render_kw={
            "placeholder": "Saisir l'e-mail du délégataire (ex: nom@exemple.fr)"
        },
        validators=[validators.DataRequired()],
    )
    add_delegate = ButtonField("")


class SearchForm(B3DeskForm):
    """A search bar, sent as a GET request."""

    class Meta:
        csrf = False
        field_template = "_search_field.html"

    find = ButtonField("")


class UserSearchForm(SearchForm):
    search = StringField(
        label=_("Rechercher un utilisateur"),
        render_kw={"placeholder": "Saisir l'une des informations du tableau"},
    )


class MeetingSearchForm(SearchForm):
    search = StringField(
        label=_("Rechercher une réunion"),
        render_kw={"placeholder": "Saisir l'une des informations du tableau"},
    )


class GroupSearchForm(SearchForm):
    search = StringField(
        label=_("Rechercher un groupe"),
        render_kw={"placeholder": "Saisir l'une des informations du tableau"},
    )


def nullable_bool(value):
    if value in (None, "", "None"):
        return None
    return value in (True, "True")


class GroupForm(B3DeskForm):
    class Meta:
        field_template = "admin/_field.html"

    name = StringField(
        label=_(
            "Nom du groupe",
        ),
        description=_("doit être unique"),
        validators=[
            validators.DataRequired(),
            validators.length(max=MAX_MEETING_NAME_LENGTH),
        ],
    )
    enable_sip = SelectField(
        label=_(
            "SIP",
        ),
        choices=[
            SelectChoice("None", "---"),
            SelectChoice("True", _("Activé")),
            SelectChoice("False", _("Désactivé")),
        ],
        coerce=nullable_bool,
        default="None",
    )
    enable_file_sharing = SelectField(
        label=_(
            "Ajout de document",
        ),
        choices=[
            SelectChoice("None", "---"),
            SelectChoice("True", _("Activé")),
            SelectChoice("False", _("Désactivé")),
        ],
        coerce=nullable_bool,
        default="None",
    )
    enable_ai_summary = SelectField(
        label=_(
            "Génération de résumé (IA)",
        ),
        choices=[
            SelectChoice("None", "---"),
            SelectChoice("True", _("Activé")),
            SelectChoice("False", _("Désactivé")),
        ],
        coerce=nullable_bool,
        default="None",
    )
    save = ButtonField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_sip.description = (
            _("Activé par défaut")
            if current_app.config["ENABLE_SIP"]
            else _("Désactivé par défaut")
        )
        if not current_app.config["FQDN_SIP_SERVER"]:
            self.enable_sip.description = _(
                "Non disponible : aucun serveur SIP configuré (FQDN_SIP_SERVER)"
            )
            self.enable_sip.render_kw = {"disabled": True}
        self.enable_file_sharing.description = (
            _("Activé par défaut")
            if current_app.config["FILE_SHARING"]
            else _("Désactivé par défaut")
        )
        self.enable_ai_summary.description = (
            _("Activé par défaut")
            if current_app.config["ENABLE_AI_SUMMARY"]
            else _("Désactivé par défaut")
        )
