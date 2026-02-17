import datetime
import json
from typing import Annotated
from typing import Any

from flask_babel import lazy_gettext as _
from pydantic import BeforeValidator
from pydantic import FilePath
from pydantic import PositiveInt
from pydantic import ValidationInfo
from pydantic import computed_field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


def split_comma_separated_strings(value):
    """Convert a comma-separated string into a list of stripped strings."""
    if not isinstance(value, str):
        return value

    return map(str.strip, value.split(","))


ListOfStrings = Annotated[list[str], BeforeValidator(split_comma_separated_strings)]


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

    LOG_CONFIG: FilePath | None = None
    """Chemin vers un fichier de configuration de logs Python.

    Le fichier doit être au :ref:`format de fichiers de logs officiel Python <logging-config-fileformat>`.
    Il peut être au format INI ou à partir de Python 3.11 au format TOML (qui est recommandé):

    .. tip:: Par défaut les images Docker montent le répertoire ``web/conf`` dans ``/opt/bbb-visio/conf``.
        On peut donc créer un fichier ``web/conf/logging.toml`` dans le projet avec la configuration voulue.
        On indiquera ensuite ``LOG_CONFIG=/opt/bbb-visio/conf/logging.toml`` pour que ce fichier soit chargé
        par l'image Docker.

    .. note:: `[root]` désigne un logger par défaut qui traite tous les messages de log qui ne sont pas traités par d'autres loggers.

    .. code-block:: toml
        :caption: Exemple de fichier de configuration de logs au format toml

        version = 1

        [formatters.default]
        format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

        [handlers.wsgi]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/wsgi.log"
        formatter = "default"

        [handlers.b3desk]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/b3desk.log"
        formatter = "default"

        [loggers.b3desk]
        level = "INFO"
        handlers = ["b3desk"]

        [root]
        level = "INFO"
        handlers = ["wsgi"]

    .. code-block:: toml
        :caption: Exemple de configuration avec un fichier destiné aux erreurs

        version = 1

        [formatters.default]
        format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

        [handlers.wsgi]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/wsgi.log"
        formatter = "default"

        [handlers.b3desk]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/b3desk.log"
        formatter = "default"

        [handlers.errors]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/errors.log"
        formatter = "default"
        level = "WARNING"

        [loggers.b3desk]
        level = "INFO"
        handlers = ["b3desk", "errors"]

        [root]
        level = "INFO"
        handlers = ["wsgi"]

    .. code-block:: toml
        :caption:
            Exemple de configuration avec les logs BBB dans un fichier dédié,
            avec DEBUG sur le module BBB uniquement.

        version = 1

        [formatters.default]
        format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

        [handlers.wsgi]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/wsgi.log"
        formatter = "default"

        [handlers.bbb]
        class = "logging.handlers.WatchedFileHandler"
        filename = "/var/log/bbb.log"
        formatter = "default"

        [loggers.bbb]
        level = "DEBUG"
        handlers = ["bbb"]

        [loggers.b3desk]
        level = "INFO"
        handlers = ["wsgi"]

        [root]
        level = "INFO"
        handlers = ["wsgi"]

    """

    REDIS_URL: str | None = None
    """L’URL du serveur redis utilisé pour les tâches asynchrones.

    Par exemple ``localhost:6379``.
    """

    NC_LOGIN_TIMEDELTA_DAYS: int = 30
    """Durée en jours avant l’expiration des autorisations Nextcloud."""

    NC_LOGIN_API_URL: str | None = None
    """URL du fournisseur d'accès utilisé par Nextcloud.

    Par exemple ``https://auth.example.org``.
    """

    NC_LOGIN_API_KEY: str | None = None
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

    WTF_CSRF_TIME_LIMIT: int = 3600 * 24
    """Indique en secondes la durée de validité des jetons CSRF.

    Il est nécessaire de mettre une valeur plus élevée que le délai de
    mise en cache des pages par le serveur web. Sans quoi les
    navigateurs des utilisateurs serviront des pages en caches contenant
    des jetons CSRF expirés.

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

    ALLOWED_MIME_TYPES_SERVER_SIDE: list[str] | None = [
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
        allowed_mime_types_server_side: list[str] | None,
        info: ValidationInfo,
    ) -> list[str]:
        """Return allowed MIME types parsed from string or list."""
        if not allowed_mime_types_server_side:
            return []

        if isinstance(allowed_mime_types_server_side, str):
            return json.loads(allowed_mime_types_server_side)

        return allowed_mime_types_server_side

    ACCEPTED_FILES_CLIENT_SIDE: str | None = (
        "image/*,.pdf,.doc,.docx,.htm,.html,.odp,.ods,.odt,.ppt,.pptx,.xls,.xlsx"
    )
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

    OIDC_SCOPES: ListOfStrings = ["openid", "email", "profile"]
    """Liste des scopes OpenID Connect pour lesquels une autorisation sera
    demandée au serveur d’identité, séparés par des virgules.

    Passé en paramètre ``auth_request_params`` de flask-pyoidc.
    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/api.html#module-flask_pyoidc.provider_configuration
    """

    OIDC_USERINFO_HTTP_METHOD: str = "POST"
    """Méthode ``GET`` ou ``POST`` à utiliser pour les requêtes sur le point
    d’entrée *UserInfo* du serveur d’identité.

    Plus d’infos sur
    https://flask-pyoidc.readthedocs.io/en/latest/api.html?highlight=userinfo_http_method#flask_pyoidc.provider_configuration.ProviderConfiguration
    """

    OIDC_INFO_REQUESTED_FIELDS: list[str] = ["email", "given_name", "family_name"]
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_ISSUER: str | None = None
    """URL du serveur d’identité des organisateurs de réunion.

    Par exemple : https://auth.example.com
    """

    OIDC_AUTH_URI: str | None = None
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_USERINFO_URI: str | None = None
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_TOKEN_URI: str | None = None
    """Probablement un relicat de flask-oidc, semble inutilisé."""

    OIDC_CLIENT_ID: str | None = None
    """ID du client auprès du serveur d’identité des organisateurs."""

    OIDC_CLIENT_SECRET: str | None = None
    """Secret permettant d’identifier le client auprès du serveur d’identité
    des organisateurs."""

    OIDC_CLIENT_AUTH_METHOD: str | None = "client_secret_post"
    """Méthode de communication avec le point d’entrée ``token_endpoint`` du
    serveur d’identité des organisateurs."""

    OIDC_INTROSPECTION_AUTH_METHOD: str = "client_secret_basic"
    """Méthode de communication avec le point d’entrée d’introspection
    ``token_introspection`` du serveur d’identité des organisateurs."""

    # TODO: replace by OIDCAuthentication.redirect_uri_config
    OIDC_REDIRECT_URI: str | None = None
    """URL de B3Desk vers laquelle le serveur d’identité redirige les
    utilisateurs après authentification.

    Par exemple ``https://visio-test.education.fr/oidc_callback``

    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/configuration.html?highlight=OIDC_REDIRECT_URI#static-client-registration
    """

    OIDC_SERVICE_NAME: str | None = None
    """Probablement un relicat de flask-oidc, semble inutilisé à part en valeur
    par défaut de ``OIDC_ATTENDEE_SERVICE_NAME``."""

    # Attendee OIDC Configuration (back to default if empty)
    OIDC_ATTENDEE_ENABLED: bool | None = True
    """Indique si le serveur d’authentification des participants est activé ou
    non.

    Si le serveur est KO, en passant cette variable à ``False``,
    l’authentification ne sera plus nécessaire pour les liens d’invitation authentifiés, ce qui permet de faire en sorte que les liens restent valides.
    """

    OIDC_ATTENDEE_ISSUER: str | None = None
    """URL du serveur d’identité des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_ISSUER``.
    """

    OIDC_ATTENDEE_CLIENT_ID: str | None = None
    """ID du client auprès du serveur d’identité des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_CLIENT_ID``.
    """

    OIDC_ATTENDEE_CLIENT_SECRET: str | None = None
    """Secret permettant d’identifier le client auprès du serveur d’identité
    des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_CLIENT_ID``.
    """

    OIDC_ATTENDEE_CLIENT_AUTH_METHOD: str | None = None
    """Méthode de communication avec le point d’entrée ``token_endpoint`` du
    serveur d’identité des participants authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_CLIENT_AUTH_METHOD``.
    """

    OIDC_ATTENDEE_INTROSPECTION_AUTH_METHOD: str = "client_secret_basic"
    """Méthode de communication avec le point d’entrée d’introspection
    ``token_introspection`` du serveur d’identité  des participants
    authentifiés.

    Si non renseigné, prend la valeur de ``OIDC_INTROSPECTION_AUTH_METHOD``.
    """

    OIDC_ATTENDEE_USERINFO_HTTP_METHOD: str | None = None
    """Méthode ``GET`` ou ``POST`` à utiliser pour les requêtes sur le point
    d’entrée *UserInfo* du serveur d’identité.

    Si non renseigné, prend la valeur de ``OIDC_USERINFO_HTTP_METHOD``.

    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/api.html?highlight=userinfo_http_method#flask_pyoidc.provider_configuration.ProviderConfiguration
    """

    OIDC_ATTENDEE_SERVICE_NAME: str | None = None
    """Nom du service d’authentification des participants authentifiés. Utilisé
    pour l’affichage dans la modale d’invitation de participants authentifés.

    Si non renseigné, prend la valeur de ``OIDC_SERVICE_NAME``.
    """

    OIDC_ATTENDEE_SCOPES: ListOfStrings | None = None
    """Liste des scopes OpenID Connect pour lesquels une autorisation sera
    demandée au serveur d’identité des participants authentifiés, séparés par
    des virgules.

    Si non renseigné, prend la valeur de ``OIDC_SCOPES``.

    Passé en paramètre ``auth_request_params`` de flask-pyoidc.
    Plus d’infos sur https://flask-pyoidc.readthedocs.io/en/latest/api.html#module-flask_pyoidc.provider_configuration
    """

    SECONDARY_IDENTITY_PROVIDER_ENABLED: bool | None = False
    """Indique si un second serveur d'identité pour la connection a un
    Nextcloud est activée.

    S'il y a bien besoin de ce second serveur d'identité pour connecter
    un utilisateur sur un Nextcloud, l'identifiant Nextcloud de
    l'utilisateur sera recherché à partir de son mail.
    """

    SECONDARY_IDENTITY_PROVIDER_URI: str | None = None
    """Url du serveur d'identité permettant de retrouver un id utilisateur à
    partir de son email."""

    SECONDARY_IDENTITY_PROVIDER_REALM: str | None = None
    """Groupe sous lequel est enregistré l'utilisateur."""

    SECONDARY_IDENTITY_PROVIDER_CLIENT_ID: str | None = None
    """ID du client B3desk dans ce serveur d'identité."""

    SECONDARY_IDENTITY_PROVIDER_CLIENT_SECRET: str | None = None
    """Secret du client B3desk dans ce serveur d'identité."""

    @field_validator("OIDC_ATTENDEE_ISSUER")
    def get_attendee_issuer(cls, attendee_issuer: str, info: ValidationInfo) -> str:
        """Return OIDC_ISSUER if attendee issuer is not specified."""
        return attendee_issuer or info.data.get("OIDC_ISSUER")

    @field_validator("OIDC_ATTENDEE_CLIENT_ID")
    def get_attendee_client_id(
        cls, attendee_client_id: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_CLIENT_ID if attendee client ID is not specified."""
        return attendee_client_id or info.data.get("OIDC_CLIENT_ID")

    @field_validator("OIDC_ATTENDEE_CLIENT_SECRET")
    def get_attendee_client_secret(
        cls, attendee_client_secret: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_CLIENT_SECRET if attendee client secret is not specified."""
        return attendee_client_secret or info.data.get("OIDC_CLIENT_SECRET")

    @field_validator("OIDC_ATTENDEE_CLIENT_AUTH_METHOD")
    def get_attendee_client_auth_method(
        cls, attendee_client_auth_method: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_CLIENT_AUTH_METHOD if attendee client auth method is not specified."""
        return attendee_client_auth_method or info.data.get("OIDC_CLIENT_AUTH_METHOD")

    @field_validator("OIDC_ATTENDEE_INTROSPECTION_AUTH_METHOD")
    def get_attendee_introspection_endpoint_auth_method(
        cls, attendee_introspection_endpoint_auth_method: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_INTROSPECTION_AUTH_METHOD if attendee introspection auth method is not specified."""
        return attendee_introspection_endpoint_auth_method or info.data.get(
            "OIDC_INTROSPECTION_AUTH_METHOD"
        )

    @field_validator("OIDC_ATTENDEE_USERINFO_HTTP_METHOD")
    def get_attendee_userinfo_http_method(
        cls, attendee_userinfo_http_method: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_USERINFO_HTTP_METHOD if attendee userinfo HTTP method is not specified."""
        return attendee_userinfo_http_method or info.data.get(
            "OIDC_USERINFO_HTTP_METHOD"
        )

    @field_validator("OIDC_ATTENDEE_SERVICE_NAME")
    def get_attendee_attendee_service_name(
        cls, attendee_attendee_service_name: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_SERVICE_NAME if attendee service name is not specified."""
        return attendee_attendee_service_name or info.data.get("OIDC_SERVICE_NAME")

    @field_validator("OIDC_ATTENDEE_SCOPES")
    def get_attendee_attendee_scopes(
        cls, attendee_scopes: str, info: ValidationInfo
    ) -> str:
        """Return OIDC_SCOPES if attendee scopes are not specified."""
        return attendee_scopes or info.data.get("OIDC_SCOPES")

    DOCUMENTATION_LINK_URL: str | None = None
    """Surcharge l’adresse de la page de documentation si renseigné."""

    DOCUMENTATION_LINK_LABEL: str | None = None
    """Semble inutilisé."""

    @computed_field
    def DOCUMENTATION_LINK(self) -> dict[str, Any]:
        """Return documentation link metadata including URL and external flag."""
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

    MEETING_LOGOUT_URL: str | None = None
    """URL vers laquelle sont redirigés les utilisateurs après un séminaire."""

    SATISFACTION_POLL_URL: str | None = None
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

    MEETING_LOCALE_VARIANT: str = ""
    """Variante de locale pour le vocabulaire des réunions.

    Peut être *cours* ou *séminaire*.
    Si vide : réunion par défaut.
    """

    WELCOME_PAGE_SUBTITLE: Any = _("Mes salles de réunion")
    """Formulation du sous-titre de la page de création de réunion."""

    MEETING_MAIL_SUBJECT: Any = _(
        "Invitation à une réunion en ligne immédiate du Webinaire de l’Etat"
    )
    """Formulation du titre du mail d’invitation à une réunion."""

    FILE_SHARING: bool = False
    """Active la fonctionnalité de téléversement de fichiers."""

    DOCUMENTATION_PAGE_SUBTITLE: str | None = None
    """Sous-titre de la page de documentation."""

    QUICK_MEETING: bool = True
    """Affiche le lien de création de réunions improvisées."""

    QUICK_MEETING_DEFAULT_NAME: Any = _("Réunion improvisée")
    """Nom par défaut des réunions improvisées."""

    QUICK_MEETING_MODERATOR_LINK_INTRODUCTION: Any = _(" Lien Modérateur  ")
    """Formulation de « Lien Modérateur » dans les liens BBB."""

    QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION: Any = _(" Lien Participant  ")
    """Formulation de « Lien Participant » dans les liens BBB."""

    QUICK_MEETING_MODERATOR_WELCOME_MESSAGE: Any = _(
        "Bienvenue aux modérateurs. Pour inviter quelqu'un à cette réunion, envoyez-lui l'un de ces liens :"
    )
    """Formulation du message d’accueil aux modérateurs dans BBB."""

    QUICK_MEETING_LOGOUT_URL: str | None = None
    """Lien vers lequel sont redirigés les participants à la fin d’une réunion
    improvisée.

    Par défaut, c'est la page d'accueil du service B3Desk.
    """

    MAILTO_LINKS: bool = False
    """Affiche des liens vers les adresses email des modérateurs et
    participants dans la liste des réunions."""

    SHORTY: bool = False
    """Affichage court des listes de réunions."""

    CLIPBOARD: bool = False
    """Semble inutilisé."""

    RECORDING: bool = False
    """Active la fonctionnalité d’enregistrement des réunions."""

    RECORDING_DURATION: datetime.timedelta | None = datetime.timedelta(days=365)
    """Durée par défaut de conservation des enregistrements.

    Utilisé à des fins d’affichage seulement.
    """

    BETA: bool = False
    """Active l'encart « Bêta » dans l'entête du service B3Desk."""

    SMTP_FROM: str | None = None
    """Adresse email d’expéditeur pour les mails d’invitation."""

    SMTP_HOST: str | None = None
    """Addresse du serveur SMTP."""

    SMTP_PORT: int | None = None
    """Port du serveur SMTP."""

    SMTP_USERNAME: str | None = None
    """Identifiant auprès du serveur SMTP."""

    SMTP_PASSWORD: str | None = None
    """Mot de passe du serveur SMTP."""

    SMTP_SSL: bool | None = False
    """Connexion SSL au serveur SMTP."""

    SMTP_STARTTLS: bool | None = False
    """Connexion StartTLS au serveur SMTP."""

    DEFAULT_MEETING_DURATION: int = 280
    """Durée maximum en minutes des réunion passée à l'API BBB.

    Plus d’informations sur
    https://docs.bigbluebutton.org/development/api/#create
    """

    RIE_NETWORK_IPS: ListOfStrings | None = None
    """Plages d’adresses IP du réseau interministériel de l'État.

    Affiche un encart particulier pour les utilisateurs se connectant
    depuis ce réseau.
    """

    MAX_PARTICIPANTS: int = 200
    """Nombre moyen de participants indicatif sur la plateforme.

    Seulement utilisé à des fins d’affichage.
    """

    STATS_CACHE_DURATION: int = 1800
    """Durée de rétention du cache des statistiques des réunions."""

    STATS_URL: str | None = None
    """URL du fichier de statistiques des réunions.

    Par exemple ``https://visio-test.education.fr/static/local/stats.csv``
    """

    STATS_INDEX: int = 2
    """Numéro de ligne des statistiques de réunion dans le fichier CSV."""

    BIGBLUEBUTTON_ENDPOINT: str | None = None
    """URL du service BBB.

    Par exemple ``https://bbb30.test/bigbluebutton/api``
    """

    BIGBLUEBUTTON_SECRET: str | None = None
    """Mot de passe du service BBB."""

    BIGBLUEBUTTON_DIALNUMBER: str | None = None
    """The dial access number that participants can call in using regular
    phone.

    Required if pin management is enabled.
    """

    BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL: str | None = None
    """Passé à l'API BBB via le paramètre ``meta_analytics-callback-url``.

    Plus d’informations sur
    https://docs.bigbluebutton.org/development/api/#create
    """

    BIGBLUEBUTTON_API_CACHE_DURATION: int = 5
    """Le temps de mise en cache (en secondes) des réponses aux requêtes GET à
    l'API BBB."""

    BIGBLUEBUTTON_REQUEST_TIMEOUT: int = 2
    """BBB request timeout

    Timeout for BBB request expressed in seconds in logs
    """

    MATOMO_URL: str | None = None
    """URL de l’instance de Matomo vers laquelle envoyer des statistiques."""

    MATOMO_SITE_ID: str | None = None
    """ID de l’instance B3Desk dans Matomo."""

    SENTRY_DSN: str | None = None
    """Sentry DSN to catch exceptions."""

    ENABLE_LASUITENUMERIQUE: bool | None = False
    """Enable LaSuite numerique homepage style."""

    ENABLE_PIN_MANAGEMENT: bool | None = False
    """Enable mangement of PIN by B3Desk.

    PIN allows users joining meeting by phone. BIGBLUEBUTTON_DIALNUMBER
    required if PIN management enabled.
    """

    @field_validator("ENABLE_PIN_MANAGEMENT", mode="before")
    def dial_number_required(
        cls,
        enable_pin_management: bool | None,
        info: ValidationInfo,
    ) -> bool:
        """Validate that BIGBLUEBUTTON_DIALNUMBER is set when PIN management is enabled."""
        if enable_pin_management:
            assert info.data["BIGBLUEBUTTON_DIALNUMBER"], (
                "BIGBLUEBUTTON_DIALNUMBER configuration required when enabling pin management"
            )
        return enable_pin_management

    FQDN_SIP_SERVER: str | None = None
    """FQDN SIP server.

    Required if SIP is enabled.
    """

    PRIVATE_KEY: str | None = None
    """Private key generated by joserfc, double quotes are mandatory.

    It will be used to generate a token for SIPMediaGW connection
    security. Changing the private-key makes all tokens invalid.
    Required if SIP is enabled.
    """

    ENABLE_SIP: bool | None = False
    """Enable SIPMediaGW.

    SIPMediaGW url allows users connecting SIPMediaGW. FQDN_SIP_SERVER
    required if SIP enabled.
    """

    @field_validator("ENABLE_SIP", mode="after")
    def fqdn_sip_server_required(
        cls,
        enable_sip: bool | None,
        info: ValidationInfo,
    ) -> bool:
        """Validate that FQDN_SIP_SERVER is set when SIP is enabled."""
        if enable_sip and not info.data["FQDN_SIP_SERVER"]:
            raise ValueError(
                "FQDN_SIP_SERVER configuration required when enabling SIPMediaGW"
            )
        return enable_sip

    @field_validator("ENABLE_SIP", mode="after")
    def private_key_server_required(
        cls,
        enable_sip: bool | None,
        info: ValidationInfo,
    ) -> bool:
        """Validate that PRIVATE_KEY is set when SIP is enabled."""
        if enable_sip and not info.data["PRIVATE_KEY"]:
            raise ValueError(
                "PRIVATE_KEY configuration required when enabling SIPMediaGW"
            )
        return enable_sip

    VIDEO_STREAMING_LINKS: dict[str, str] | None = {}
    """List of streaming service for video sharing."""

    @field_validator("VIDEO_STREAMING_LINKS", mode="before")
    def get_video_streaming_links(
        cls,
        video_streaming_links: dict[str, str] | None,
        info: ValidationInfo,
    ) -> dict[str, str]:
        """Return video streaming links parsed from JSON string or as dictionary."""
        if not video_streaming_links:
            return {}

        if isinstance(video_streaming_links, str):
            return json.loads(video_streaming_links)

        return video_streaming_links

    PISTE_OAUTH_CLIENT_ID: str | None = None
    """Piste Oauth client_id

    Oauth client id can be retrieved from the PISTE site under APPLICATION on
    the following line: Identifiants Oauth
    """

    PISTE_OAUTH_CLIENT_SECRET: str | None = None
    """ Piste Oauth client_secret

    Oauth client secret can be retrieved from the PISTE site under APPLICATION on
    the following line: Identifiants Oauth
    under the following column: Secret Key
    """

    CAPTCHETAT_API_URL: str | None = "https://api.piste.gouv.fr/piste/"
    """PISTE API url

    basic url for PISTE API used to get and check captchetat
    """

    PISTE_OAUTH_API_URL: str | None = "https://oauth.piste.gouv.fr/api"
    """ PISTE OAUTH APU url

    basic url for PISTE OAUTH API used to get access token to captchetat API
    """

    CAPTCHA_NUMBER_ATTEMPTS: PositiveInt | None = 5
    """Captcha number attemps

    Number of attempts to enter the visio-code before submitting a captcha
    """

    CONTACT_LINK: str | None = None
    """Contact link

    If entered, a 'contact' button wil appear in footer
    """
