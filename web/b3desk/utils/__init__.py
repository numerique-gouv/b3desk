import random
import smtplib
import string
import time
from datetime import UTC
from datetime import datetime
from email.message import EmailMessage
from functools import wraps

import httpx2
from flask import abort
from flask import current_app
from flask import flash
from flask import has_request_context
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import format_datetime
from flask_babel import lazy_gettext as _
from itsdangerous import BadSignature
from itsdangerous.url_safe import URLSafeSerializer
from joserfc.errors import BadSignatureError
from joserfc.errors import DecodeError
from joserfc.errors import InvalidClaimError
from joserfc.jwk import RSAKey
from joserfc.jwt import JWTClaimsRegistry
from joserfc.jwt import decode
from netaddr import IPAddress
from netaddr import IPNetwork
from slugify import slugify
from werkzeug.routing import BaseConverter

from b3desk.models import db

HTTP_TIMEOUT = 10
DOWNLOAD_MAX_DURATION = 60
DOWNLOAD_CHUNK_SIZE = 64 * 1024


def http_client():
    """Return the HTTP client shared by the whole process, built on first use.

    In local development environment, services are not served as https, so
    certificate verification is disabled.
    """
    client = current_app.extensions.get("http_client")
    if client is None:
        client = current_app.extensions["http_client"] = httpx2.Client(
            timeout=HTTP_TIMEOUT,
            verify=not current_app.debug,
            follow_redirects=True,
        )
    return client


def download_url_to_path(url, path):
    """Download an external URL into a local path, bounded in time and in size.

    Return False when the download failed or grew past MAX_SIZE_UPLOAD. The
    client timeout only bounds the delay between two chunks, so a slow trickle
    is caught by the deadline instead.
    """
    max_size = current_app.config["MAX_SIZE_UPLOAD"]
    deadline = time.monotonic() + DOWNLOAD_MAX_DURATION
    downloaded = 0

    try:
        with http_client().stream("GET", url) as response:
            if not response.is_success:
                current_app.logger.warning(
                    "URL file download for %s returned status %s",
                    url,
                    response.status_code,
                )
                return False

            with path.open("wb") as f:
                for chunk in response.iter_bytes(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if time.monotonic() > deadline:
                        current_app.logger.warning(
                            "URL file download for %s exceeded %s seconds",
                            url,
                            DOWNLOAD_MAX_DURATION,
                        )
                        return False

                    downloaded += len(chunk)
                    if downloaded > max_size:
                        current_app.logger.warning(
                            "URL file download for %s exceeded %s bytes", url, max_size
                        )
                        return False

                    f.write(chunk)
    except httpx2.HTTPError as request_error:
        current_app.logger.warning(
            "URL file download failed for %s: %s", url, request_error
        )
        return False

    return True


def utcnow():
    """Return the current UTC time as a naive datetime, the way it is stored."""
    return datetime.now(UTC).replace(tzinfo=None)


def secret_key():
    """Return the application's secret key from configuration."""
    return current_app.config["SECRET_KEY"]


def is_rie():
    """Check wether the request was made from inside the state network "Réseau Interministériel de l'État"."""
    if not has_request_context() or not request.remote_addr:
        return False

    return current_app.config["RIE_NETWORK_IPS"] and any(
        IPAddress(request.remote_addr) in IPNetwork(str(network_ip))
        for network_ip in current_app.config["RIE_NETWORK_IPS"]
        if network_ip
    )


def get_random_alphanumeric_string(length):
    """Generate a random alphanumeric string of specified length."""
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for i in range(length))


def make_smtp():
    return {
        "from_email": current_app.config["SMTP_FROM"],
        "host": current_app.config["SMTP_HOST"],
        "port": current_app.config["SMTP_PORT"],
        "ssl": current_app.config["SMTP_SSL"],
        "starttls": current_app.config["SMTP_STARTTLS"],
        "username": current_app.config["SMTP_USERNAME"],
        "password": current_app.config["SMTP_PASSWORD"],
        "timeout": current_app.config["SMTP_TIMEOUT"],
    }


def send_delegation_mail(meeting, delegate, new_delegation: bool):
    """Send email to inform of the new delegate status."""
    smtp = make_smtp()
    msg = EmailMessage()
    body_file = (
        "mail_add_delegation_body" if new_delegation else "mail_remove_delegation_body"
    )
    context = {
        "meeting": meeting,
        "delegate": delegate,
        "welcome_url": url_for("public.welcome", _external=True),
    }
    text = render_template(f"meeting/mailto/{body_file}.txt", **context)
    html = render_template(f"meeting/mailto/{body_file}.html", **context)
    msg["Subject"] = (
        str(_(f"Nouvelle délégation pour {meeting.name}"))
        if new_delegation
        else str(_(f"Retrait de délégation pour {meeting.name}"))
    )
    msg["From"] = smtp["from_email"]
    msg["To"] = delegate.email

    send_email(msg, text, html, smtp)


def _build_recording_links(playbacks):
    """Return an ordered list of {label, url} entries from a BBB playbacks dict."""
    links = []
    if "presentation" in playbacks:
        links.append(
            {
                "label": _("Présentation interactive"),
                "url": playbacks["presentation"]["url"],
            }
        )
    if "video" in playbacks:
        video = playbacks["video"]
        links.append(
            {
                "label": _("Vidéo (téléchargement direct)"),
                "url": video.get("direct_link", video["url"]),
            }
        )
    if "ai-summary" in playbacks:
        summary = playbacks["ai-summary"]
        links.append({"label": _("Compte-rendu (HTML)"), "url": summary["url"]})
        if "pdf" in summary:
            links.append({"label": _("Compte-rendu (PDF)"), "url": summary["pdf"]})
        if "md" in summary:
            links.append({"label": _("Compte-rendu (Markdown)"), "url": summary["md"]})
    return links


def send_available_recording_notification_mail(
    meeting, playbacks, recording_name, recording_start
):
    """Send email to notify the recording is available, listing every available format."""
    recording_links = _build_recording_links(playbacks)
    if not recording_links:
        current_app.logger.warning(
            "No usable playback format for meeting %s, skipping notification mail",
            meeting.id,
        )
        return

    smtp = make_smtp()
    msg = EmailMessage()
    body_file = "mail_available_recording_notification_body"
    context = {
        "meeting": meeting,
        "recording_links": recording_links,
        "recording_name": recording_name,
        "recording_start": format_datetime(
            datetime.fromisoformat(recording_start), format="medium"
        ),
        "welcome_url": url_for("public.welcome", _external=True),
    }
    text = render_template(f"meeting/mailto/{body_file}.txt", **context)
    html = render_template(f"meeting/mailto/{body_file}.html", **context)
    msg["Subject"] = str(
        _("Votre enregistrement pour {name}").format(name=meeting.name)
    )
    msg["From"] = smtp["from_email"]
    msg["To"] = meeting.owner.email

    send_email(msg, text, html, smtp)


def send_email(msg, text, html, smtp):
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    connection_func = smtplib.SMTP_SSL if smtp["ssl"] else smtplib.SMTP
    try:
        with connection_func(
            smtp["host"], smtp["port"], timeout=smtp["timeout"]
        ) as smtp_connect:
            if smtp["starttls"]:
                smtp_connect.starttls()
            if smtp["username"]:
                smtp_connect.login(smtp["username"], smtp["password"])
            smtp_connect.send_message(msg)
        current_app.logger.info("Email sent to %s", msg["To"])
    except (smtplib.SMTPException, OSError) as e:
        current_app.logger.error(
            "Failed to send email to %s via SMTP host %s: %s",
            msg["To"],
            smtp["host"],
            e,
        )


def model_converter(model):
    """Create a Flask URL converter for database model instances."""

    class ModelConverter(BaseConverter):
        # Restricting the URL part to digits keeps non numeric identifiers from
        # reaching the database, where they would raise a DataError instead of
        # a 404. All the converted models have an integer primary key.
        regex = r"\d+"

        def __init__(self, *args, required=True, **kwargs):
            self.required = required
            super().__init__(self, *args, **kwargs)

        def to_url(self, instance):
            return str(instance.id) if instance.id else None

        def to_python(self, identifier):
            instance = db.session.get(model, identifier)
            if self.required and not instance:
                abort(404)

            return instance

    return ModelConverter


def enum_converter(enum):
    """Create a Flask URL converter for enum values."""

    class EnumConverter(BaseConverter):
        def __init__(self, *args, required=True, **kwargs):
            self.required = required
            super().__init__(self, *args, **kwargs)

        def to_url(self, instance):
            return slugify(instance.value)

        def to_python(self, identifier):
            for item in enum:
                if identifier == slugify(item.value):
                    return item
            abort(404)
            return None

    return EnumConverter


class SignedConverter(BaseConverter):
    """Flask URL converter that signs/unsigns values with itsdangerous."""

    salt = "signed"

    def to_url(self, value):
        serializer = URLSafeSerializer(secret_key(), salt=self.salt)
        return serializer.dumps(value)

    def to_python(self, signed_value):
        serializer = URLSafeSerializer(secret_key(), salt=self.salt)
        try:
            return serializer.loads(signed_value)
        except BadSignature:
            abort(404)


def check_private_key():
    """Check if private key is configured when SIP is enabled."""

    def decorator_func(initial_func):
        @wraps(initial_func)
        def wrapper_func(*args, **kwargs):
            if (
                current_app.config["ENABLE_SIP"]
                and not current_app.config["PRIVATE_KEY"]
            ):
                message = _(
                    "La clé privée n'a pas été configurée dans les paramètres "
                    "B3Desk pour sécuriser la connexion SIPMediaGW"
                )
                flash(message, "error")

            return initial_func(*args, **kwargs)

        return wrapper_func

    return decorator_func


def check_token_errors(token):
    """Validate JWT token signature and claims against application's private key.

    Returns error message if token is invalid, empty string otherwise.
    """
    error_message = ""
    if token is None:
        error_message = "No token provided"
    else:
        private_key_from_settings = RSAKey.import_key(current_app.config["PRIVATE_KEY"])
        public_key = private_key_from_settings.as_dict(private=False)
        public_key_obj = RSAKey.import_key(public_key)
        try:
            decoded_token = decode(token, public_key_obj)
            instance_url = (
                f"{current_app.config['PREFERRED_URL_SCHEME']}"
                f"://{current_app.config['SERVER_NAME']}"
            )
            claims_requests = JWTClaimsRegistry(iss={"value": instance_url})
            claims_requests.validate(decoded_token.claims)
        except DecodeError as err:
            error_message = f"This is not a valid JWT. JoseRFC error: {err}"
        except BadSignatureError as err:
            error_message = (
                f"The token is not recognized by the private key. JoseRFC error: {err}"
            )
        except InvalidClaimError as err:
            error_message = (
                f"The token must be generated by: {instance_url}, "
                f"not by {decoded_token.claims}. JoseRFC error: {err}"
            )
    if error_message:
        current_app.logger.error(error_message)
    return error_message
