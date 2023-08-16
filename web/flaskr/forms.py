from flask import current_app
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    Form,
    IntegerField,
    SelectField,
    StringField,
    TextAreaField,
    MultipleFileField,
    BooleanField,
    HiddenField,
    validators,
)


class JoinMeetingAsRoleForm(Form):
    role = SelectField(choices=["attendee", "moderator"])
    meeting_id = IntegerField()


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
        label=lazy_gettext(
            "Titre %(of_the_meeting)s",
            of_the_meeting=current_app.config["WORDING_OF_THE_MEETING"],
        ),
        description=lazy_gettext(
            "Créer %(a_meeting)s dont le titre est :",
            a_meeting=current_app.config["WORDING_A_MEETING"],
        ),
        default=lazy_gettext(
            "%(my_meeting)s",
            my_meeting=current_app.config["WORDING_MY_MEETING"].title(),
        ),
        validators=[validators.DataRequired()],
    )
    welcome = TextAreaField(
        label=lazy_gettext("Texte de bienvenue"),
        description=lazy_gettext(
            "Ce texte apparait comme message de bienvenue sur le tchat public"
        ),
        default=lazy_gettext(
            "Bienvenue dans %(this_meeting)s %(meeting_name)s.",
            this_meeting=current_app.config["WORDING_THIS_MEETING"],
            meeting_name="<u><strong> %%CONFNAME%% </strong></u>",
        ),
        render_kw={"rows": 3},
        validators=[
            validators.length(max=150, message=lazy_gettext("Le texte est trop long"))
        ],
    )
    maxParticipants = IntegerField(
        label=lazy_gettext("Nombre maximal de participants"),
        description=lazy_gettext(
            "Limitez vos salons à 250 personnes pour plus de confort"
        ),
        default=100,
    )
    duration = IntegerField(
        label=lazy_gettext("Durée maximale en minutes"),
        description=lazy_gettext(
            "Après laquelle %(the_meeting)s stoppe automatiquement",
            the_meeting=current_app.config["WORDING_THE_MEETING"],
        ),
        default=280,
        validators=[validators.NumberRange(min=1, max=999)],
    )
    guestPolicy = BooleanField(
        label=lazy_gettext("Salle d'attente"),
        description=lazy_gettext(
            "Placer les participants dans une salle d'attente lorsqu'ils rejoignent %(the_meeting)s. L'organisateur ou le modérateur devra les accepter individuellement.",
            the_meeting=current_app.config["WORDING_THE_MEETING"],
        ),
        default=False,
    )
    webcamsOnlyForModerator = BooleanField(
        label=lazy_gettext(
            "Seul les modérateurs peuvent voir les webcams des autres participants"
        ),
        description=lazy_gettext(
            "Les participants ne verront pas la diffusion de la caméra des autres"
        ),
        default=False,
    )
    muteOnStart = BooleanField(
        label=lazy_gettext("Micros fermés au démarrage"),
        description=lazy_gettext(
            "Les micros sont clos à la connexion des utilisateurs"
        ),
        default=True,
    )
    lockSettingsDisableCam = BooleanField(
        label=lazy_gettext("Verrouillage caméra"),
        description=lazy_gettext(
            "Les participants ne pourront pas activer leur caméra"
        ),
        default=False,
    )
    lockSettingsDisableMic = BooleanField(
        label=lazy_gettext("Verrouillage micro"),
        description=lazy_gettext("Les participants ne pourront pas activer leur micro"),
        default=False,
    )
    lockSettingsDisablePrivateChat = BooleanField(
        label=lazy_gettext("Désactivation de la discussion privée"),
        description=lazy_gettext(
            "Interdit les échanges textes directs entre participants"
        ),
        default=False,
    )
    lockSettingsDisablePublicChat = BooleanField(
        label=lazy_gettext("Désactivation de la discussion publique"),
        description=lazy_gettext("Pas de tchat"),
        default=False,
    )
    lockSettingsDisableNote = BooleanField(
        label=lazy_gettext("Désactivation de la prise de notes"),
        description=lazy_gettext("Pas de prise de notes collaborative"),
        default=False,
    )
    moderatorOnlyMessage = TextAreaField(
        label=lazy_gettext("Message à l'attention des modérateurs"),
        description=lazy_gettext("150 caractères max"),
        default=lazy_gettext("Bienvenue aux modérateurs"),
        validators=[
            validators.length(max=150, message=lazy_gettext("Le message est trop long"))
        ],
        render_kw={"rows": 3},
    )
    logoutUrl = StringField(
        label=lazy_gettext(
            "Url de redirection après %(the_meeting)s",
            the_meeting=current_app.config["WORDING_THE_MEETING"],
        ),
        default=current_app.config["MEETING_LOGOUT_URL"],
    )
    moderatorPW = StringField(
        label=lazy_gettext("Renouveler le lien modérateur"),
        description=lazy_gettext(
            "Ce code vous permet si vous le changez de bloquer les anciens liens"
        ),
        default="Pa55W0rd1",
        render_kw={"readonly": True},
        validators=[validators.DataRequired()],
    )
    attendeePW = StringField(
        label=lazy_gettext("Renouveler le lien participants"),
        description=lazy_gettext(
            "Ce code vous permet si vous le changez de bloquer les anciens liens"
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
        label=lazy_gettext("Enregistrement manuel"),
        description=lazy_gettext(
            "Autoriser le démarrage et l'arrêt de l'enregistrement par le modérateur"
        ),
        default=False,
    )
    autoStartRecording = BooleanField(
        label=lazy_gettext("Enregistrement automatique"),
        description=lazy_gettext("Démarrage automatique"),
        default=False,
    )


class RecordingForm(FlaskForm):
    name = StringField(
        validators=[validators.DataRequired()], label="Nom de l'enregistrement"
    )


class EndMeetingForm(FlaskForm):
    meeting_id = HiddenField()
