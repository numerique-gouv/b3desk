from flask import current_app
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import Form
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators


class JoinMeetingForm(FlaskForm):
    fullname = StringField()
    meeting_fake_id = StringField()
    user_id = IntegerField()
    h = StringField()
    fullname_suffix = StringField()


class JoinMailMeetingForm(JoinMeetingForm):
    expiration = IntegerField()


class ShowMeetingForm(Form):
    meeting_id = IntegerField()


class MeetingFilesForm(FlaskForm):
    url = TextAreaField(
        label="Lien web du fichier à ajouter",
        description="Le lien web à entrer doit permettre de télécharger un fichier",
        render_kw={"rows": 1, "placeholder": "https://exemple.com/image.jpg"},
        validators=[validators.length(max=255, message="Le texte est trop long")],
    )
    guestPolicy = BooleanField(
        label="Salle d'attente",
        description="Placer les participants dans une salle d'attente lorsqu'ils rejoignent "
        + current_app.config["WORDING_THE_MEETING"]
        + ". L'organisateur ou le modérateur devra les accepter individuellement.",
        default=False,
    )


class MeetingForm(FlaskForm):
    id = IntegerField()
    name = StringField(
        label=_(
            "Nom %(of_the_meeting)s",
            of_the_meeting=current_app.config["WORDING_OF_THE_MEETING"],
        ),
        description=_(
            "Vous ne pourrez plus changer ce titre une fois la salle créée. Ce nom est visible des participents",
            a_meeting=current_app.config["WORDING_A_MEETING"],
        ),
        default=_(
            "%(my_meeting)s",
            my_meeting=current_app.config["WORDING_MY_MEETING"].title(),
        ),
        validators=[validators.DataRequired()],
    )
    welcome = TextAreaField(
        label=_("Texte de bienvenue"),
        description=_(
            "Ce texte apparait comme message de bienvenue sur le tchat public. 150 caractères max."
        ),
        default=_(
            "Bienvenue dans %(this_meeting)s %(meeting_name)s.",
            this_meeting=current_app.config["WORDING_THIS_MEETING"],
            meeting_name="<u><strong> %%CONFNAME%% </strong></u>",
        ),
        render_kw={"rows": 3},
        validators=[validators.length(max=150, message=_("Le texte est trop long"))],
    )
    maxParticipants = IntegerField(
        label=_("Nombre maximal de participants"),
        description=_("Limitez vos salons à 350 personnes pour plus de confort."),
        default=350,
    )
    duration = IntegerField(
        label=_("Durée maximale (minutes)"),
        description=_(
            "A l'issue de cette durée %(the_meeting)s stoppe automatiquement. 1h = 60, 2h = 120, 3h = 180, 4h = 240.",
            the_meeting=current_app.config["WORDING_THE_MEETING"],
        ),
        default=280,
        validators=[validators.NumberRange(min=1, max=999)],
    )
    guestPolicy = BooleanField(
        label=_("Salle d'attente"),
        description=_(
            "Placer les participants dans une salle d'attente lorsqu'ils rejoignent %(the_meeting)s. L'organisateur ou le modérateur devra les accepter individuellement.",
            the_meeting=current_app.config["WORDING_THE_MEETING"],
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
        default=False,
    )
    lockSettingsDisableMic = BooleanField(
        label=_("Micros des participants"),
        description=_(
            "Vous pouvez autoriser ou interdire l'ouverture du microphone des participants."
        ),
        default=False,
    )
    lockSettingsDisablePrivateChat = BooleanField(
        label=_("Discussions privées"),
        default=False,
    )
    lockSettingsDisablePublicChat = BooleanField(
        label=_("Discussion publique (tchat)"),
        default=False,
    )
    lockSettingsDisableNote = BooleanField(
        label=_("Prise de note collaborative"),
        default=False,
    )
    moderatorOnlyMessage = TextAreaField(
        label=_("Message à l'attention des modérateurs"),
        description=_("150 caractères max"),
        default=_("Bienvenue aux modérateurs"),
        validators=[validators.length(max=150, message=_("Le message est trop long"))],
        render_kw={"rows": 3},
    )
    logoutUrl = StringField(
        label=_(
            "Url de redirection après %(the_meeting)s",
            the_meeting=current_app.config["WORDING_THE_MEETING"],
        ),
        default=current_app.config["MEETING_LOGOUT_URL"],
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logoutUrl.default = current_app.config["MEETING_LOGOUT_URL"]


class MeetingWithRecordForm(MeetingForm):
    allowStartStopRecording = BooleanField(
        label=_("Enregistrement manuel"),
        description=_(
            "Vous pouvez lancer ou arrêter à tout moment l'enregistrement de la salle."
        ),
        default=False,
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
        validators=[validators.DataRequired()], label="Nom de l'enregistrement"
    )


class EndMeetingForm(FlaskForm):
    meeting_id = HiddenField()
