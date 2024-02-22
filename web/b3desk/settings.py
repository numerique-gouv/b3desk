import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from b3desk.constants import DEFAULT_EMAIL_WHITELIST
from flask_babel import lazy_gettext as _
from pydantic import computed_field
from pydantic import field_validator
from pydantic import ValidationInfo
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

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
        "reunion": _("une réunion improvisée"),
        "seminaire": "un séminaire improvisé",
    },
    "A_QUICK_MEETING": {
        "cours": "un cours immédiat",
        "reunion": _("une réunion immédiate"),
        "seminaire": "un séminaire immédiat",
    },
    "PRIVATE_MEETINGS": {
        "cours": "cours privés",
        "reunion": _("réunions privées"),
        "seminaire": "séminaires privés",
    },
    "GOOD_MEETING": {
        "cours": "bon cours",
        "reunion": _("bonne réunion"),
        "seminaire": "bon séminaire",
    },
    "MEETING_UNDEFINED_ARTICLE": {
        "cours": "un",
        "reunion": _("une"),
        "seminaire": "un",
    },
    "A_MEETING_TO_WHICH": {
        "cours": "un cours auquel",
        "reunion": _("une réunion à laquelle"),
        "seminaire": "un séminaire auquel",
    },
    "WELCOME_PAGE_SUBTITLE": {
        "cours": _(
            "Créez en un clic un cours aux réglages standards. Il ne sera pas enregistré dans votre liste de salles."
        ),
        "reunion": _(
            "Créez en un clic une réunion aux réglages standards. Elle ne sera pas enregistrée dans votre liste de salles."
        ),
        "seminaire": _(
            "Créez en un clic un séminaire aux réglages standards. Il ne sera pas enregistré dans votre liste de salles."
        ),
    },
    "MEETING_MAIL_SUBJECT": {
        "cours": _("Invitation à un cours en ligne immédiat du Webinaire de l’Etat"),
        "reunion": _(
            "Invitation à une réunion en ligne immédiat du Webinaire de l’Etat"
        ),
        "seminaire": _(
            "Invitation à un séminaire en ligne immédiat du Webinaire de l’Etat"
        ),
    },
}


class MainSettings(BaseSettings):
    """Paramètres de configuration du frontal B3Desk."""

    model_config = SettingsConfigDict(extra="allow")

    SECRET_KEY: str
    """Clé secrète utilisée notamment pour la signature des cookies. Cette clé
    DOIT être différente pour TOUTES les instances de B3Desk, et être tenue
    secrète. Peut être générée avec ``python -c 'import secrets;
    print(secrets.token_hex())'``

    Plus d'infos sur
    https://flask.palletsprojects.com/en/3.0.x/config/#SECRET_KEY
    """

    SERVER_NAME: str
    """Le nom de domaine sur lequel est déployé l'instance B3Desk.

    Par exemple ``b3desk.example.org``, sans `https://`.

    Plus d'infos sur https://flask.palletsprojects.com/en/3.0.x/config/#SERVER_NAME.
    """

    PREFERRED_URL_SCHEME: str = "https"
    """La méthode préférée utilisée pour générer des URL. Peut être `http` ou
    `https`.

    Plus d'infos sur
    https://flask.palletsprojects.com/en/3.0.x/config/#PREFERRED_URL_SCHEME.
    """

    REDIS_URL: Optional[str] = None
    """L’URL du serveur redis utilisé pour les tâches asynchrones.

    Par exemple ``localhost:6379``.
    """

    NC_LOGIN_TIMEDELTA_DAYS: int = 30
    """Durée en jours avant l’expiration des autorisations Nextcloud."""

    NC_LOGIN_API_URL: Optional[str] = None
    """URL du fournisseur d'accès utilisé par Nextcloud.

    Par exemple ``https://auth.example.org``.
    """

    NC_LOGIN_API_KEY: Optional[str] = None
    """Clé d'API Nextcloud."""

    FORCE_HTTPS_ON_EXTERNAL_URLS: bool = False
    """Force le protocole https pour les URLs Nextcloud."""

    UPLOAD_DIR: str
    """Chemin vers le dossier dans lequel seront stockés les fichiers
    téléversés par les utilisateurs."""

    TMP_DOWNLOAD_DIR: str
    """Chemin vers un dossier qui servira de stockage temporaire de fichiers
    entre Nextcloud et BBB."""

    MAX_SIZE_UPLOAD: int = 20000000
    """Taille maximum des fichiers téléversés, en octets."""

    TIME_FORMAT: str = "%Y-%m-%d"
    """Format des dates utilisées lors des échanges avec l’API de Nextcloud.

    Plus d’informations sur
    https://docs.python.org/fr/3/library/datetime.html#strftime-and-strptime-format-codes
    """

    TESTING: bool = False
    """Mode tests unitaires, à ne surtout pas utiliser en production.

    Plus d’informations sur
    https://flask.palletsprojects.com/en/3.0.x/config/#TESTING
    """

    DEBUG: bool = False
    """Mode debug, à ne surtout pas utiliser en production.

    Plus d’informations sur
    https://flask.palletsprojects.com/en/3.0.x/config/#DEBUG
    """

    TITLE: str = "BBB-Visio"
    """Titre HTML par défaut pour les pages HTML."""

    EXTERNAL_UPLOAD_DESCRIPTION: str = "Fichiers depuis votre Nextcloud"
    """Description dans BBB des fichiers téléversés dans Nextcloud."""

    WTF_CSRF_TIME_LIMIT: int = 3600 * 12
    """Indique en secondes la durée de validit des jetons CSRF.

    Plus d'infos sur
    https://flask-wtf.readthedocs.io/en/1.2.x/config/
    """

    BABEL_TRANSLATION_DIRECTORIES: str = "/opt/bbb-visio/translations"
    """Un ou plusieurs chemins vers les répertoires des catalogues de
    traduction, séparés par des « ; ».

    Plus d’infos sur
    https://python-babel.github.io/flask-babel/#configuration
    """

    MAX_MEETINGS_PER_USER: int = 50
    """Le nombre maximum de séminaires que peut créer un utilisateur."""

    ALLOWED_MIME_TYPES_SERVER_SIDE: Optional[List[str]] = [
        "application/pdf",
        "image/vnd.dwg",
        "image/x-xcf",
        "image/jpeg",
        "image/jpx",
        "image/png",
        "image/apng",
        "image/gif",
        "image/webp",
        "image/x-canon-cr2",
        "image/tiff",
        "image/bmp",
        "image/vnd.ms-photo",
        "image/vnd.adobe.photoshop",
        "image/x-icon",
        "image/heic",
        "image/avif",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
    ]
    """Liste de mime-types acceptés par le serveur pour le téléversement de
    fichiers.

    Si non renseigné, tous les fichiers sont autorisés.
    """

    @field_validator("ALLOWED_MIME_TYPES_SERVER_SIDE", mode="before")
    def get_allowed_mime_types_server_side(
        cls,
        allowed_mime_types_server_side: Optional[List[str]],
        info: ValidationInfo,
    ) -> List[str]:
        if not allowed_mime_types_server_side:
            return []

        if isinstance(allowed_mime_types_server_side, str):
            return json.loads(allowed_mime_types_server_side)

        return allowed_mime_types_server_side

    ACCEPTED_FILES_CLIENT_SIDE: Optional[
        str
    ] = "image/*,.pdf,.doc,.docx,.htm,.html,.odp,.ods,.odt,.ppt,.pptx,.xls,.xlsx"
    """Liste de mime-types autorisés par le navigateur pour le téléversement
    des fichiers, séparés par des virgules.

    Passé en paramètre ``acceptedFiles`` de *Dropzone*.

    Plus d’infos sur https://docs.dropzone.dev/configuration/basics/configuration-options
    """

    OIDC_ID_TOKEN_COOKIE_SECURE: bool = False
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_REQUIRE_VERIFIED_EMAIL: bool = False
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_USER_INFO_ENABLED: bool = True
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_OPENID_REALM: str = "apps"
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_SCOPES: List[str] = ["openid", "email", "profile"]
    """Liste des scopes OpenID Connect pour lesquels une autorisation sera
    demandée au serveur d’identité, séparés par des virgules.

    Passé en paramètre ``auth_request_params`` de flask-pyoidc.
    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/api.html#module-flask_pyoidc.provider_configuration
    """

    @field_validator("OIDC_SCOPES", mode="before")
    def get_oidc_scopes(cls, oidc_scopes: List[str], info: ValidationInfo) -> str:
        return oidc_scopes.split(",") if isinstance(oidc_scopes, str) else oidc_scopes

    OIDC_INTROSPECTION_AUTH_METHOD: str = "client_secret_post"
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_USERINFO_HTTP_METHOD: str = "POST"
    """Méthode ``GET`` ou ``POST`` à utiliser pour les requêtes sur le point
    d’entrée *UserInfo* du serveur d’identité.

    Plus d’infos sur
    https://flask-pyoidc.readthedocs.io/en/latest/api.html?highlight=userinfo_http_method#flask_pyoidc.provider_configuration.ProviderConfiguration
    """

    OIDC_INFO_REQUESTED_FIELDS: List[str] = ["email", "given_name", "family_name"]
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_ISSUER: Optional[str] = None
    """URL du serveur d’identité des organisateurs de réunion.

    Par exemple : https://auth.example.com
    """

    OIDC_AUTH_URI: Optional[str] = None
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_USERINFO_URI: Optional[str] = None
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_TOKEN_URI: Optional[str] = None
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_CLIENT_ID: Optional[str] = None
    """ID du client auprès du serveur d’identité des organisateurs."""

    OIDC_CLIENT_SECRET: Optional[str] = None
    """Secret permettant d’identifier le client auprès du serveur d’identité
    des organisateurs."""

    OIDC_CLIENT_AUTH_METHOD: Optional[str] = "client_secret_post"
    """Méthode de communication avec le point d’entrée
    ``token_introspection_uri`` du serveur d’identité des organisateurs.

    Surcharge probablement ``OIDC_INTROSPECTION_AUTH_METHOD``.
    """

    # TODO: replace by OIDCAuthentication.redirect_uri_config
    OIDC_REDIRECT_URI: Optional[str] = None
    """URL de B3Desk vers laquelle le serveur d’identité redirige les
    utilisateurs après authentification.

    Par exemple ``http://localhost:5000/oidc_callback``

    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/configuration.html?highlight=OIDC_REDIRECT_URI#static-client-registration
    """

    OIDC_SERVICE_NAME: Optional[str] = None
    """Probablement un relicat de flask-oidc, semble inutilisé à part en valeur
    par défaut de ``OIDC_ATTENDEE_SERVICE_NAME``."""

    # Attendee OIDC Configuration (back to default if empty)
    OIDC_ATTENDEE_ENABLED: Optional[bool] = True
    """Indique si le serveur d’authentification des participants est activé ou
    non.

    Si le serveur est KO, en passant cette variable à ``False``,
    l’authentification ne sera plus nécessaire pour les liens d’invitation authentifiés, ce qui permet de faire en sorte que les liens restent valides.
    """

    OIDC_ATTENDEE_ISSUER: Optional[str] = None
    """URL du serveur d’identité des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_ISSUER``.
    """

    OIDC_ATTENDEE_CLIENT_ID: Optional[str] = None
    """ID du client auprès du serveur d’identité des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_CLIENT_ID``.
    """

    OIDC_ATTENDEE_CLIENT_SECRET: Optional[str] = None
    """Secret permettant d’identifier le client auprès du serveur d’identité
    des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_CLIENT_ID``.
    """

    OIDC_ATTENDEE_CLIENT_AUTH_METHOD: Optional[str] = None
    """Méthode de communication avec le point d’entrée
    ``token_introspection_uri`` du serveur d’identité des participants
    authentifiés. Surcharge probablement ``OIDC_INTROSPECTION_AUTH_METHOD``.

    Si non renseigné, prend la valeur de ``OIDC_CLIENT_AUTH_METHOD``.
    """

    OIDC_ATTENDEE_USERINFO_HTTP_METHOD: Optional[str] = None
    """Méthode ``GET`` ou ``POST`` à utiliser pour les requêtes sur le point
    d’entrée *UserInfo* du serveur d’identité.

    Si non renseigné, prend la valeur de ``OIDC_USERINFO_HTTP_METHOD``.

    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/api.html?highlight=userinfo_http_method#flask_pyoidc.provider_configuration.ProviderConfiguration
    """

    OIDC_ATTENDEE_SERVICE_NAME: Optional[str] = None
    """Nom du service d’authentification des participants authentifiés. Utilisé
    pour l’affichage dans la modale d’invitation de participants authentifés.

    Si non renseigné, prend la valeur de ``OIDC_SERVICE_NAME``.
    """

    OIDC_ATTENDEE_SCOPES: Optional[List[str]] = None
    """Liste des scopes OpenID Connect pour lesquels une autorisation sera
    demandée au serveur d’identité des participants authentifiés, séparés par
    des virgules.

    Si non renseigné, prend la valeur de ``OIDC_SCOPES``.

    Passé en paramètre ``auth_request_params`` de flask-pyoidc.
    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/api.html#module-flask_pyoidc.provider_configuration
    """

    @field_validator("OIDC_ATTENDEE_ISSUER")
    def get_attendee_issuer(cls, attendee_issuer: str, info: ValidationInfo) -> str:
        return attendee_issuer or info.data.get("OIDC_ISSUER")

    @field_validator("OIDC_ATTENDEE_CLIENT_ID")
    def get_attendee_client_id(
        cls, attendee_client_id: str, info: ValidationInfo
    ) -> str:
        return attendee_client_id or info.data.get("OIDC_CLIENT_ID")

    @field_validator("OIDC_ATTENDEE_CLIENT_SECRET")
    def get_attendee_client_secret(
        cls, attendee_client_secret: str, info: ValidationInfo
    ) -> str:
        return attendee_client_secret or info.data.get("OIDC_CLIENT_SECRET")

    @field_validator("OIDC_ATTENDEE_CLIENT_AUTH_METHOD")
    def get_attendee_client_auth_method(
        cls, attendee_client_auth_method: str, info: ValidationInfo
    ) -> str:
        return attendee_client_auth_method or info.data.get("OIDC_CLIENT_AUTH_METHOD")

    @field_validator("OIDC_ATTENDEE_USERINFO_HTTP_METHOD")
    def get_attendee_userinfo_http_method(
        cls, attendee_userinfo_http_method: str, info: ValidationInfo
    ) -> str:
        return attendee_userinfo_http_method or info.data.get(
            "OIDC_USERINFO_HTTP_METHOD"
        )

    @field_validator("OIDC_ATTENDEE_SERVICE_NAME")
    def get_attendee_attendee_service_name(
        cls, attendee_attendee_service_name: str, info: ValidationInfo
    ) -> str:
        return attendee_attendee_service_name or info.data.get("OIDC_SERVICE_NAME")

    @field_validator("OIDC_ATTENDEE_SCOPES")
    def get_attendee_attendee_scopes(
        cls, attendee_scopes: str, info: ValidationInfo
    ) -> str:
        scopes = attendee_scopes or info.data.get("OIDC_SCOPES")
        return scopes.split(",") if isinstance(scopes, str) else scopes

    DOCUMENTATION_LINK_URL: Optional[str] = None
    """Surcharge l’adresse de la page de documentation si renseigné."""

    DOCUMENTATION_LINK_LABEL: Optional[str] = None
    """Semble inutilisé."""

    @computed_field
    def DOCUMENTATION_LINK(self) -> Dict[str, Any]:
        return {
            "url": self.DOCUMENTATION_LINK_URL,
            "label": self.DOCUMENTATION_LINK_LABEL,
            "is_external": self.DOCUMENTATION_LINK_URL
            and self.DOCUMENTATION_LINK_URL.lower().startswith(
                ("/", "http://", "https://")
            ),
        }

    SERVICE_TITLE: str = "Webinaire"
    """Nom du service B3Desk."""

    SERVICE_TAGLINE: str = "Le service de webinaire pour les agents de l’État"
    """Slogan du service B3Desk."""

    MEETING_LOGOUT_URL: Optional[str] = None
    """URL vers laquelle sont redirigés les utilisateurs après un séminaire."""

    SATISFACTION_POLL_URL: Optional[str] = None
    """URL de l’iframe du formulaire de satisfaction."""

    SQLALCHEMY_DATABASE_URI: str
    """URI de configuration de la base de données.

    Par exemple ``postgresql://user:password@localhost:5432/bbb_visio``
    """

    # TODO: delete as this is the default in flask-sqlalchemy 3?
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    """Traçage des évènements de modification des modèles dans SQLAlchemy.

    Plus d’informations sur
    https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/track-modifications/
    """

    MEETING_KEY_WORDING: str = "reunion"
    """Nommage des réunions.

    Peut-être *reunion*, *cours* ou *séminaire*.
    """

    WORDING_A_MEETING: Any = None
    """Formulation de « une réunion », par exemple *un cours* ou *un
    séminaire*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_A_MEETING")
    def get_wording_a_meeting(cls, wording_a_meeting: Any, info: ValidationInfo) -> Any:
        return (
            wording_a_meeting
            or AVAILABLE_WORDINGS["A_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_MY_MEETING: Any = None
    """Formulation de « ma réunion », par exemple *mon cours* ou *mon
    séminaire*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_MY_MEETING")
    def get_wording_my_meeting(
        cls, wording_my_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_my_meeting
            or AVAILABLE_WORDINGS["MY_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_THE_MEETING: Any = None
    """Formulation de « la réunion », par exemple *le cours* ou *le séminaire*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_THE_MEETING")
    def get_wording_the_meeting(
        cls, wording_the_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_the_meeting
            or AVAILABLE_WORDINGS["THE_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_OF_THE_MEETING: Any = None
    """Formulation de « de la réunion », par exemple *du cours* ou *du
    séminaire*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_OF_THE_MEETING")
    def get_wording_of_the_meeting(
        cls, wording_of_the_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_of_the_meeting
            or AVAILABLE_WORDINGS["OF_THE_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_MEETING: Any = None
    """Formulation de « réunion », par exemple *cours* ou *séminaire*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_MEETING")
    def get_wording_meeting(cls, wording_meeting: Any, info: ValidationInfo) -> Any:
        return (
            wording_meeting
            or AVAILABLE_WORDINGS["MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_MEETINGS: Any = None
    """Formulation de « réunions », par exemple *cours* ou *séminaires*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_MEETINGS")
    def get_wording_meetings(cls, wording_meetings: Any, info: ValidationInfo) -> Any:
        return (
            wording_meetings
            or AVAILABLE_WORDINGS["MEETINGS"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_THIS_MEETING: Any = None
    """Formulation de « cette réunion », par exemple *ce cours* ou *ce
    séminaires*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_THIS_MEETING")
    def get_wording_this_meeting(
        cls, wording_this_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_this_meeting
            or AVAILABLE_WORDINGS["THIS_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_TO_THE_MEETING: Any = None
    """Formulation de « à la réunion », par exemple *au cours* ou *au
    séminaires*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_TO_THE_MEETING")
    def get_wording_to_the_meeting(
        cls, wording_to_the_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_to_the_meeting
            or AVAILABLE_WORDINGS["TO_THE_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_IMPROVISED_MEETING: Any = None
    """Formulation de « réunion improvisée », par exemple *cours improvisé* ou
    *séminaire improvisé*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_IMPROVISED_MEETING")
    def get_wording_improvised_meeting(
        cls, wording_improvised_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_improvised_meeting
            or AVAILABLE_WORDINGS["IMPROVISED_MEETING"][
                info.data["MEETING_KEY_WORDING"]
            ]
        )

    WORDING_AN_IMPROVISED_MEETING: Any = None
    """Formulation de « une réunion improvisée », par exemple *un cours
    improvisé* ou *un séminaire improvisé*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_AN_IMPROVISED_MEETING")
    def get_wording_an_improvised_meeting(
        cls, wording_an_improvised_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_an_improvised_meeting
            or AVAILABLE_WORDINGS["AN_IMPROVISED_MEETING"][
                info.data["MEETING_KEY_WORDING"]
            ]
        )

    WORDING_A_QUICK_MEETING: Any = None
    """Formulation de « une réunion immédiate », par exemple *un cours
    immédiat* ou *un séminaire immédiat*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_A_QUICK_MEETING")
    def get_wording_a_quick_meeting(
        cls, wording_a_quick_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_a_quick_meeting
            or AVAILABLE_WORDINGS["A_QUICK_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_PRIVATE_MEETINGS: Any = None
    """Formulation de « réunions privées », par exemple *cours privés* ou
    *séminaires privés*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_PRIVATE_MEETINGS")
    def get_wording_private_meetings(
        cls, wording_private_meetings: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_private_meetings
            or AVAILABLE_WORDINGS["PRIVATE_MEETINGS"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_GOOD_MEETING: Any = None
    """Formulation de « bonne réunion », par exemple *bon cours* ou *bon
    séminaire*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_GOOD_MEETING")
    def get_wording_good_meeting(
        cls, wording_good_meeting: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_good_meeting
            or AVAILABLE_WORDINGS["GOOD_MEETING"][info.data["MEETING_KEY_WORDING"]]
        )

    WORDING_MEETING_UNDEFINED_ARTICLE: Any = None
    """Formulation de l’article indéterminé de « réunion » comme « une », par
    exemple *un*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_MEETING_UNDEFINED_ARTICLE")
    def get_wording_meeting_undefined_article(
        cls, wording_meeting_undefined_article: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_meeting_undefined_article
            or AVAILABLE_WORDINGS["MEETING_UNDEFINED_ARTICLE"][
                info.data["MEETING_KEY_WORDING"]
            ]
        )

    WORDING_A_MEETING_TO_WHICH: Any = None
    """Formulation de « une réunion à laquelle », par exemple *un cours auquel*
    ou *un séminaire auquel*.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WORDING_A_MEETING_TO_WHICH")
    def get_wording_a_meeting_to_which(
        cls, wording_a_meeting_to_which: Any, info: ValidationInfo
    ) -> Any:
        return (
            wording_a_meeting_to_which
            or AVAILABLE_WORDINGS["A_MEETING_TO_WHICH"][
                info.data["MEETING_KEY_WORDING"]
            ]
        )

    WELCOME_PAGE_SUBTITLE: Any = None
    """Formulation du sous-titre de la page de création de réunion.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("WELCOME_PAGE_SUBTITLE")
    def get_welcome_page_subtitle(
        cls, welcome_page_subtitle: Any, info: ValidationInfo
    ) -> Any:
        return (
            welcome_page_subtitle
            or AVAILABLE_WORDINGS["WELCOME_PAGE_SUBTITLE"][
                info.data["MEETING_KEY_WORDING"]
            ]
        )

    MEETING_MAIL_SUBJECT: Any = None
    """Formulation du titre du mail d’invitation à une réunion.

    Par défaut s’adapte à ``MEETING_KEY_WORDING``.
    """

    @field_validator("MEETING_MAIL_SUBJECT")
    def get_meeting_mail_subject(
        cls, meeting_mail_subject: Any, info: ValidationInfo
    ) -> Any:
        return (
            meeting_mail_subject
            or AVAILABLE_WORDINGS["MEETING_MAIL_SUBJECT"][
                info.data["MEETING_KEY_WORDING"]
            ]
        )

    WORDING_MEETING_PRESENTATION: str = "présentation"
    """Formulation de « présentation » qui désigne les fichiers accompagnant
    les réunions."""

    WORDING_UPLOAD_FILE: str = "envoyer"
    """Semble inutilisé."""

    FILE_SHARING: bool = False
    """Active la fonctionnalité de téléversement de fichiers."""

    DOCUMENTATION_PAGE_SUBTITLE: Optional[str] = None
    """Sous-titre de la page de documentation."""

    @computed_field
    def WORDINGS(self) -> Dict[str, Any]:
        return {
            "a_meeting": self.WORDING_A_MEETING,
            "the_meeting": self.WORDING_THE_MEETING,
            "some_meetings": self.WORDING_MEETINGS,
            "of_the_meeting": self.WORDING_OF_THE_MEETING,
            "my_meeting": self.WORDING_MY_MEETING,
            "this_meeting": self.WORDING_THIS_MEETING,
            "meeting_label": self.WORDING_MEETING,
            "meeting_presentation": self.WORDING_MEETING_PRESENTATION,
            "upload_file_label": self.WORDING_UPLOAD_FILE,
            "service_title": self.SERVICE_TITLE,
            "service_tagline": self.SERVICE_TAGLINE,
            "an_improvised_meeting": self.WORDING_AN_IMPROVISED_MEETING,
            "private_meetings": self.WORDING_PRIVATE_MEETINGS,
            "a_quick_meeting": self.WORDING_A_QUICK_MEETING,
            "good_meeting": self.WORDING_GOOD_MEETING,
            "to_the_meeting": self.WORDING_TO_THE_MEETING,
            "meeting_undefined_article": self.WORDING_MEETING_UNDEFINED_ARTICLE,
            "a_meeting_to_which": self.WORDING_A_MEETING_TO_WHICH,
            "welcome_page_subtitle": self.WELCOME_PAGE_SUBTITLE,
            "documentation_page_subtitle": self.DOCUMENTATION_PAGE_SUBTITLE,
            "meeting_mail_subject": self.MEETING_MAIL_SUBJECT,
        }

    QUICK_MEETING: bool = True
    """Affiche le lien de création de réunions improvisées."""

    QUICK_MEETING_DEFAULT_NAME: Optional[str] = None
    """Nom par défaut des réunions improvisées.

    Par défaut prend la valeur de ``WORDING_IMPROVISED_MEETING``.
    """

    @field_validator("QUICK_MEETING_DEFAULT_NAME")
    def get_quick_meeting_default_value(
        cls, quick_meeting_default_value: Optional[str], info: ValidationInfo
    ) -> Any:
        return (
            quick_meeting_default_value
            or info.data["WORDING_IMPROVISED_MEETING"].capitalize()
        )

    QUICK_MEETING_MODERATOR_LINK_INTRODUCTION: Any = _(" Lien Modérateur  ")
    """Formulation de « Lien Modérateur » dans les liens BBB."""

    QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION: Any = _(" Lien Participant  ")
    """Formulation de « Lien Participant » dans les liens BBB."""

    QUICK_MEETING_MODERATOR_WELCOME_MESSAGE: Any = None
    """Formulation du message d’accueil aux modérateurs dans BBB.

    Par défaut s’adapte à ``WORDING_THIS_MEETING``.
    """

    @field_validator("QUICK_MEETING_MODERATOR_WELCOME_MESSAGE")
    def get_quick_meeting_moderator_welcome_message(
        cls,
        quick_meeting_moderator_welcome_message: Optional[str],
        info: ValidationInfo,
    ) -> Any:
        return quick_meeting_moderator_welcome_message or _(
            "Bienvenue aux modérateurs. Pour inviter quelqu'un à %(this_meeting)s, envoyez-lui l'un de ces liens :",
            this_meeting=info.data["WORDING_THIS_MEETING"],
        )

    QUICK_MEETING_LOGOUT_URL: Optional[str] = None
    """Lien vers lequel sont redirigés les participants à la fin d’une réunion
    improvisée.

    Par défaut, c’est la page d’accueil du service B3Desk.
    """

    MAIL_MODERATOR_WELCOME_MESSAGE: Any = None
    """Formulation du message d’accueil aux modérateurs dans BBB, dont le lien
    à été envoyé par mail.

    Par défaut s’adapte à ``WORDING_THIS_MEETING``.
    """

    @field_validator("MAIL_MODERATOR_WELCOME_MESSAGE")
    def get_moderator_welcome_message(
        cls, moderator_welcome_message: Optional[str], info: ValidationInfo
    ) -> Any:
        return moderator_welcome_message or _(
            "Bienvenue. Pour inviter quelqu'un à %(this_meeting)s, envoyez-lui l'un de ces liens :",
            this_meeting=info.data["WORDING_THIS_MEETING"],
        )

    MAILTO_LINKS: bool = False
    """Affiche des liens vers les adresses email des modérateurs et
    participants dans la liste des réunions."""

    SHORTY: bool = False
    """Affichage court des listes de réunions."""

    CLIPBOARD: bool = False
    """Semble inutilisé."""

    RECORDING: bool = False
    """Active la fonctionnalité d’enregistrement des réunions."""

    BETA: bool = False
    """Active l’encart « Bêta » dans l’entête du service B3Desk."""

    MAIL_MEETING: bool = False
    """Active l’organisation de réunion par envoi de liens par email."""

    SMTP_FROM: Optional[str] = None
    """Adresse email d’expéditeur pour les mails d’invitation."""

    SMTP_HOST: Optional[str] = None
    """Addresse du serveur SMTP."""

    SMTP_PORT: Optional[int] = None
    """Port du serveur SMTP."""

    SMTP_USERNAME: Optional[str] = None
    """Identifiant auprès du serveur SMTP."""

    SMTP_PASSWORD: Optional[str] = None
    """Mot de passe du serveur SMTP."""

    SMTP_SSL: Optional[bool] = False
    """Connexion SSL au serveur SMTP."""

    SMTP_STARTTLS: Optional[bool] = False
    """Connexion StartTLS au serveur SMTP."""

    EMAIL_WHITELIST: Any = None

    @field_validator("EMAIL_WHITELIST")
    def get_email_whitelist(
        cls, email_whitelist: List[str], info: ValidationInfo
    ) -> str:
        if not email_whitelist:
            return DEFAULT_EMAIL_WHITELIST
        return (
            [email_whitelist] if isinstance(email_whitelist, str) else email_whitelist
        )

    DEFAULT_MEETING_DURATION: int = 280
    """Durée maximum en minutes des réunion passée à l'API BBB.

    Plus d’informations sur
    https://docs.bigbluebutton.org/development/api/#create
    """

    RIE_NETWORK_IPS: Optional[List[str]] = None
    """Plages d’adresses IP du réseau interministériel de l'État.

    Affiche un encart particulier pour les utilisateurs se connectant
    depuis ce réseau.
    """

    @field_validator("RIE_NETWORK_IPS", mode="before")
    def get_rie_network_ips(
        cls, rie_network_ips: List[str], info: ValidationInfo
    ) -> str:
        return (
            rie_network_ips.split(",")
            if isinstance(rie_network_ips, str)
            else rie_network_ips
        )

    MAX_PARTICIPANTS: int = 200
    """Nombre moyen de participants indicatif sur la plateforme.

    Seulement utilisé à des fins d’affichage.
    """

    STATS_CACHE_DURATION: int = 1800
    """Durée de rétention du cache des statistiques des réunions."""

    STATS_URL: Optional[str] = None
    """URL du fichier de statistiques des réunions.

    Par exemple ``http://localhost:5000/static/local/stats.csv``
    """

    STATS_INDEX: int = 2
    """Numéro de ligne des statistiques de réunion dans le fichier CSV."""

    BIGBLUEBUTTON_ENDPOINT: Optional[str] = None
    """URL du service BBB.

    Par exemple ``https://bbb26.test/bigbluebutton/api``
    """

    BIGBLUEBUTTON_SECRET: Optional[str] = None
    """Mot de passe du service BBB."""

    BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL: Optional[str] = None
    """Passé à l'API BBB via le paramètre ``meta_analytics-callback-url``.

    Plus d’informations sur
    https://docs.bigbluebutton.org/development/api/#create
    """

    MATOMO_URL: Optional[str] = None
    """URL de l’instance de Matomo vers laquelle envoyer des statistiques."""

    MATOMO_SITE_ID: Optional[str] = None
    """ID de l’instance B3Desk dans Matomo."""
