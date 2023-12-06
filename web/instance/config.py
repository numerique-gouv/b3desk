import json
import os

from flask_babel import lazy_gettext
from flaskr.constants import DEFAULT_EMAIL_WHITELIST


# App configuration
SECRET_KEY = os.environ.get("SECRET_KEY")
NC_LOGIN_TIMEDELTA_DAYS = int(os.environ.get("NC_LOGIN_TIMEDELTA_DAYS"))
REDIS_URL = os.environ.get("REDIS_URL")
NC_LOGIN_API_URL = os.environ.get("NC_LOGIN_API_URL")
NC_LOGIN_API_KEY = os.environ.get("NC_LOGIN_API_KEY")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
TMP_DOWNLOAD_DIR = os.environ.get("TMP_DOWNLOAD_DIR")
MAX_SIZE_UPLOAD = os.environ.get("MAX_SIZE_UPLOAD")
TIME_FORMAT = os.environ.get("TIME_FORMAT")
TESTING = True
DEBUG = True
TITLE = os.environ.get("TITLE")
SERVER_FQDN = os.environ.get("SERVER_FQDN")
EXTERNAL_UPLOAD_DESCRIPTION = os.environ.get("EXTERNAL_UPLOAD_DESCRIPTION")
WTF_CSRF_TIME_LIMIT = int(os.environ.get("WTF_CSRF_TIME_LIMIT", 3600 * 12))
MAX_MEETINGS_PER_USER = int(os.environ.get("MAX_MEETINGS_PER_USER", 50))

ALLOWED_MIME_TYPES_SERVER_SIDE = json.loads(
    os.environ.get("ALLOWED_MIME_TYPES_SERVER_SIDE", "[]") or "[]"
)
ACCEPTED_FILES_CLIENT_SIDE = os.environ.get("ACCEPTED_FILES_CLIENT_SIDE", "")

# Default OIDC Configuration
OIDC_ID_TOKEN_COOKIE_SECURE = False
OIDC_REQUIRE_VERIFIED_EMAIL = False
OIDC_USER_INFO_ENABLED = True
OIDC_OPENID_REALM = os.environ.get("OIDC_OPENID_REALM")
OIDC_SCOPES = (
    list(map(str.strip, os.environ["OIDC_SCOPES"].split(",")))
    if os.environ.get("OIDC_SCOPES")
    else [
        "openid",
        "email",
        "profile",
    ]
)
OIDC_INTROSPECTION_AUTH_METHOD = "client_secret_post"
OIDC_USERINFO_HTTP_METHOD = os.environ.get("OIDC_USERINFO_HTTP_METHOD")
OIDC_INFO_REQUESTED_FIELDS = ["email", "given_name", "family_name"]
OIDC_ISSUER = os.environ.get("OIDC_ISSUER")
OIDC_AUTH_URI = os.environ.get("OIDC_AUTH_URI")
OIDC_USERINFO_URI = os.environ.get("OIDC_USERINFO_URI")
OIDC_TOKEN_URI = os.environ.get("OIDC_TOKEN_URI")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID")
OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET")
OIDC_CLIENT_AUTH_METHOD = os.environ.get("OIDC_CLIENT_AUTH_METHOD")
OIDC_REDIRECT_URI = os.environ.get("OIDC_REDIRECT_URI")
OIDC_SERVICE_NAME = os.environ.get("OIDC_SERVICE_NAME")

# Attendee OIDC Configuration (back to default if empty)
OIDC_ATTENDEE_ENABLED = os.environ.get("OIDC_ATTENDEE_ENABLED") not in [
    0,
    False,
    "0",
    "false",
    "False",
    "off",
    "OFF",
]
OIDC_ATTENDEE_ISSUER = os.environ.get("OIDC_ATTENDEE_ISSUER") or OIDC_ISSUER
OIDC_ATTENDEE_CLIENT_ID = os.environ.get("OIDC_ATTENDEE_CLIENT_ID") or OIDC_CLIENT_ID
OIDC_ATTENDEE_CLIENT_SECRET = (
    os.environ.get("OIDC_ATTENDEE_CLIENT_SECRET") or OIDC_CLIENT_SECRET
)
OIDC_ATTENDEE_CLIENT_AUTH_METHOD = (
    os.environ.get("OIDC_ATTENDEE_CLIENT_AUTH_METHOD") or OIDC_CLIENT_AUTH_METHOD
)
OIDC_ATTENDEE_USERINFO_HTTP_METHOD = (
    os.environ.get("OIDC_ATTENDEE_USERINFO_HTTP_METHOD") or OIDC_USERINFO_HTTP_METHOD
)
OIDC_ATTENDEE_SERVICE_NAME = (
    os.environ.get("OIDC_ATTENDEE_SERVICE_NAME") or OIDC_SERVICE_NAME
)
OIDC_ATTENDEE_SCOPES = (
    list(map(str.strip, os.environ["OIDC_ATTENDEE_SCOPES"].split(",")))
    if os.environ.get("OIDC_ATTENDEE_SCOPES")
    else OIDC_SCOPES
)

# Links
DOCUMENTATION_LINK = {
    "url": os.environ.get("DOCUMENTATION_LINK_URL"),
    "label": os.environ.get("DOCUMENTATION_LINK_LABEL"),
    "is_external": not os.environ.get("DOCUMENTATION_LINK_URL")
    .lower()
    .startswith(("/", SERVER_FQDN.lower())),
}
SERVICE_TITLE = os.environ.get("SERVICE_TITLE")
SERVICE_TAGLINE = os.environ.get("SERVICE_TAGLINE")

MEETING_LOGOUT_URL = os.environ.get("MEETING_LOGOUT_URL", "")
SATISFACTION_POLL_URL = os.environ.get("SATISFACTION_POLL_URL")

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# wording
MEETING_KEY_WORDING = os.environ.get("MEETING_KEY_WORDING", "reunion")

AVAILABLE_WORDINGS = {
    "MEETING": {"cours": "cours", "reunion": "réunion", "seminaire": "séminaire"},
    "MEETINGS": {"cours": "cours", "reunion": "réunions", "seminaire": "séminaires"},
    "A_MEETING": {
        "cours": "un cours",
        "reunion": "une réunion",
        "seminaire": "un séminaire",
    },
    "MY_MEETING": {
        "cours": "mon cours",
        "reunion": "ma réunion",
        "seminaire": "mon séminaire",
    },
    "THE_MEETING": {
        "cours": "le cours",
        "reunion": "la réunion",
        "seminaire": "le séminaire",
    },
    "OF_THE_MEETING": {
        "cours": "du cours",
        "reunion": "de la réunion",
        "seminaire": "du séminaire",
    },
    "THIS_MEETING": {
        "cours": "ce cours",
        "reunion": "cette réunion",
        "seminaire": "ce séminaire",
    },
    "TO_THE_MEETING": {
        "cours": "au cours",
        "reunion": "à la réunion",
        "seminaire": "au séminaire",
    },
    "IMPROVISED_MEETING": {
        "cours": "cours improvisé",
        "reunion": "réunion improvisée",
        "seminaire": "séminaire improvisé",
    },
    "AN_IMPROVISED_MEETING": {
        "cours": "un cours improvisé",
        "reunion": lazy_gettext("une réunion improvisée"),
        "seminaire": "un séminaire improvisé",
    },
    "A_QUICK_MEETING": {
        "cours": "un cours immédiat",
        "reunion": lazy_gettext("une réunion immédiate"),
        "seminaire": "un séminaire immédiat",
    },
    "PRIVATE_MEETINGS": {
        "cours": "cours privés",
        "reunion": lazy_gettext("réunions privées"),
        "seminaire": "séminaires privés",
    },
    "GOOD_MEETING": {
        "cours": "bon cours",
        "reunion": lazy_gettext("bonne réunion"),
        "seminaire": "bon séminaire",
    },
    "MEETING_UNDEFINED_ARTICLE": {
        "cours": "un",
        "reunion": lazy_gettext("une"),
        "seminaire": "un",
    },
    "A_MEETING_TO_WHICH": {
        "cours": "un cours auquel",
        "reunion": lazy_gettext("une réunion à laquelle"),
        "seminaire": "un séminaire auquel",
    },
    "WELCOME_PAGE_SUBTITLE": {
        "cours": lazy_gettext(
            "Créez un cours immédiatement avec des réglages standards. Ce cours ne sera pas enregistré dans votre liste de salons."
        ),
        "reunion": lazy_gettext(
            "Créez une réunion immédiatement avec des réglages standards. Cette réunion ne sera pas enregistrée dans votre liste de salons."
        ),
        "seminaire": lazy_gettext(
            "Créez un séminaire immédiatement avec des réglages standards. Ce séminaire ne sera pas enregistré dans votre liste de salons."
        ),
    },
    "MEETING_MAIL_SUBJECT": {
        "cours": lazy_gettext(
            "Invitation à un cours en ligne immédiat du Webinaire de l’Etat"
        ),
        "reunion": lazy_gettext(
            "Invitation à une réunion en ligne immédiat du Webinaire de l’Etat"
        ),
        "seminaire": lazy_gettext(
            "Invitation à un séminaire en ligne immédiat du Webinaire de l’Etat"
        ),
    },
}


WORDING_A_MEETING = AVAILABLE_WORDINGS["A_MEETING"][MEETING_KEY_WORDING]
WORDING_MY_MEETING = AVAILABLE_WORDINGS["MY_MEETING"][MEETING_KEY_WORDING]
WORDING_THE_MEETING = AVAILABLE_WORDINGS["THE_MEETING"][MEETING_KEY_WORDING]
WORDING_OF_THE_MEETING = AVAILABLE_WORDINGS["OF_THE_MEETING"][MEETING_KEY_WORDING]
WORDING_MEETING = AVAILABLE_WORDINGS["MEETING"][MEETING_KEY_WORDING]
WORDING_MEETINGS = AVAILABLE_WORDINGS["MEETINGS"][MEETING_KEY_WORDING]
WORDING_THIS_MEETING = AVAILABLE_WORDINGS["THIS_MEETING"][MEETING_KEY_WORDING]
WORDING_TO_THE_MEETING = AVAILABLE_WORDINGS["TO_THE_MEETING"][MEETING_KEY_WORDING]
WORDING_IMPROVISED_MEETING = AVAILABLE_WORDINGS["IMPROVISED_MEETING"][
    MEETING_KEY_WORDING
]
WORDING_AN_IMPROVISED_MEETING = AVAILABLE_WORDINGS["AN_IMPROVISED_MEETING"][
    MEETING_KEY_WORDING
]
WORDING_A_QUICK_MEETING = AVAILABLE_WORDINGS["A_QUICK_MEETING"][MEETING_KEY_WORDING]
WORDING_PRIVATE_MEETINGS = AVAILABLE_WORDINGS["PRIVATE_MEETINGS"][MEETING_KEY_WORDING]
WORDING_GOOD_MEETING = AVAILABLE_WORDINGS["GOOD_MEETING"][MEETING_KEY_WORDING]
WORDING_MEETING_UNDEFINED_ARTICLE = AVAILABLE_WORDINGS["MEETING_UNDEFINED_ARTICLE"][
    MEETING_KEY_WORDING
]
WORDING_A_MEETING_TO_WHICH = AVAILABLE_WORDINGS["A_MEETING_TO_WHICH"][
    MEETING_KEY_WORDING
]
WELCOME_PAGE_SUBTITLE = AVAILABLE_WORDINGS["WELCOME_PAGE_SUBTITLE"][MEETING_KEY_WORDING]
MEETING_MAIL_SUBJECT = AVAILABLE_WORDINGS["MEETING_MAIL_SUBJECT"][MEETING_KEY_WORDING]

WORDING_MEETING_PRESENTATION = os.environ.get(
    "WORDING_MEETING_PRESENTATION", "présentation"
)
WORDING_UPLOAD_FILE = os.environ.get("WORDING_MEETING_UPLOAD_FILE", "envoyer")

FILE_SHARING = os.environ.get("FILE_SHARING") == "on"

DOCUMENTATION_PAGE_SUBTITLE = os.environ.get("DOCUMENTATION_PAGE_SUBTITLE")
WORDINGS = {
    "a_meeting": WORDING_A_MEETING,
    "the_meeting": WORDING_THE_MEETING,
    "some_meetings": WORDING_MEETINGS,
    "of_the_meeting": WORDING_OF_THE_MEETING,
    "my_meeting": WORDING_MY_MEETING,
    "this_meeting": WORDING_THIS_MEETING,
    "meeting_label": WORDING_MEETING,
    "meeting_presentation": WORDING_MEETING_PRESENTATION,
    "upload_file_label": WORDING_UPLOAD_FILE,
    "service_title": SERVICE_TITLE,
    "service_tagline": SERVICE_TAGLINE,
    "an_improvised_meeting": WORDING_AN_IMPROVISED_MEETING,
    "private_meetings": WORDING_PRIVATE_MEETINGS,
    "a_quick_meeting": WORDING_A_QUICK_MEETING,
    "good_meeting": WORDING_GOOD_MEETING,
    "to_the_meeting": WORDING_TO_THE_MEETING,
    "meeting_undefined_article": WORDING_MEETING_UNDEFINED_ARTICLE,
    "a_meeting_to_which": WORDING_A_MEETING_TO_WHICH,
    "welcome_page_subtitle": WELCOME_PAGE_SUBTITLE,
    "documentation_page_subtitle": DOCUMENTATION_PAGE_SUBTITLE,
    "meeting_mail_subject": MEETING_MAIL_SUBJECT,
}

# quick meeting
QUICK_MEETING = True
QUICK_MEETING_DEFAULT_NAME = WORDING_IMPROVISED_MEETING.capitalize()
QUICK_MEETING_MODERATOR_LINK_INTRODUCTION = lazy_gettext(" Lien Modérateur  ")
QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION = lazy_gettext(" Lien Participant  ")
QUICK_MEETING_MODERATOR_WELCOME_MESSAGE = lazy_gettext(
    "Bienvenue aux modérateurs. Pour inviter quelqu'un à %(this_meeting)s, envoyez-lui l'un de ces liens :",
    this_meeting=WORDING_THIS_MEETING,
)
QUICK_MEETING_LOGOUT_URL = os.environ.get("QUICK_MEETING_LOGOUT_URL")
MAIL_MODERATOR_WELCOME_MESSAGE = lazy_gettext(
    "Bienvenue. Pour inviter quelqu'un à %(this_meeting)s, envoyez-lui l'un de ces liens :",
    this_meeting=WORDING_THIS_MEETING,
)
MAILTO_LINKS = False
SHORTY = False
CLIPBOARD = os.environ.get("CLIPBOARD") == "on"
RECORDING = os.environ.get("RECORDING") == "on"
BETA = os.environ.get("BETA") == "on"
MAIL_MEETING = os.environ.get("MAIL_MEETING") == "on"
SMTP_FROM = os.environ.get("SMTP_FROM")
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = os.environ.get("SMTP_PORT")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SSL = os.environ.get("SMTP_SSL")
EMAIL_WHITELIST = os.environ.get("EMAIL_WHITELIST")
DEFAULT_MEETING_DURATION = os.environ.get("DEFAULT_MEETING_DURATION", 280)

RIE_NETWORK_IPS = os.environ.get("RIE_NETWORK_IPS", "").split(",")
MAX_PARTICIPANTS = os.environ.get("MAX_PARTICIPANTS", 200)
STATS_CACHE_DURATION = int(os.environ.get("STATS_CACHE_DURATION", 1800))
STATS_URL = os.environ.get("STATS_URL")
STATS_INDEX = int(os.environ.get("STATS_INDEX", 2))

# Big Blue Button configuration
BIGBLUEBUTTON_ENDPOINT = os.environ.get("BIGBLUEBUTTON_ENDPOINT")
BIGBLUEBUTTON_SECRET = os.environ.get("BIGBLUEBUTTON_SECRET")
BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL = os.environ.get(
    "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
)

BABEL_TRANSLATION_DIRECTORIES = "/opt/bbb-visio/translations"

EMAIL_WHITELIST = DEFAULT_EMAIL_WHITELIST
