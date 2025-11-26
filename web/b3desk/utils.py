import random
import re
import smtplib
import string
from email.message import EmailMessage
from email.mime.text import MIMEText
from functools import wraps

from flask import abort
from flask import current_app
from flask import flash
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import lazy_gettext as _
from flask_pyoidc.pyoidc_facade import PyoidcFacade
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
from b3desk.models.roles import Role


def secret_key():
    """Return the application's secret key from configuration."""
    return current_app.config["SECRET_KEY"]


def is_rie():
    """Check wether the request was made from inside the state network "Réseau Interministériel de l'État"."""
    if not request.remote_addr:
        return False

    return current_app.config["RIE_NETWORK_IPS"] and any(
        IPAddress(request.remote_addr) in IPNetwork(str(network_ip))
        for network_ip in current_app.config["RIE_NETWORK_IPS"]
        if network_ip
    )


def is_accepted_email(email):
    """Check if email matches any regex pattern in the configured whitelist."""
    for regex in current_app.config["EMAIL_WHITELIST"]:
        if re.search(regex, email):
            return True
    return False


def is_valid_email(email):
    """Validate email address format using regex pattern."""
    if not email or not re.search(
        r"^([a-zA-Z0-9_\-\.']+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$", email
    ):
        return False
    return True


def get_random_alphanumeric_string(length):
    """Generate a random alphanumeric string of specified length."""
    letters_and_digits = string.ascii_letters + string.digits
    result_str = "".join(random.choice(letters_and_digits) for i in range(length))
    return result_str


def make_smtp():
    return {
        "from_email": current_app.config["SMTP_FROM"],
        "host": current_app.config["SMTP_HOST"],
        "port": current_app.config["SMTP_PORT"],
        "ssl": current_app.config["SMTP_SSL"],
        "starttls": current_app.config["SMTP_STARTTLS"],
        "username": current_app.config["SMTP_USERNAME"],
        "password": current_app.config["SMTP_PASSWORD"],
    }


def send_quick_meeting_mail(meeting, to_email):
    """Send quick meeting invitation email with meeting access link."""
    smtp = make_smtp()
    wordings = current_app.config["WORDINGS"]
    msg = EmailMessage()
    content = render_template(
        "meeting/mailto/mail_quick_meeting_body.txt",
        role=Role.moderator,
        moderator_mail_signin_url=meeting.get_mail_signin_url(),
        welcome_url=url_for("public.welcome", _external=True),
        meeting=meeting,
    )
    msg["Subject"] = str(wordings["meeting_mail_subject"])
    msg["From"] = smtp["from_email"]
    msg["To"] = to_email

    send_email(msg, content, smtp)


def send_delegation_mail(meeting, delegate, new_delegation: bool):
    """Send email to inform of the new delegate status."""
    smtp = make_smtp()
    msg = EmailMessage()
    body_file = (
        "mail_add_delegation_body.txt"
        if new_delegation
        else "mail_remove_delegation_body.txt"
    )
    content = render_template(
        f"meeting/mailto/{body_file}",
        meeting=meeting,
        delegate=delegate,
        welcome_url=url_for("public.welcome", _external=True),
    )
    msg["Subject"] = (
        str(_(f"Nouvelle délégation pour {meeting.name}"))
        if new_delegation
        else str(_(f"Retrait de délégation pour {meeting.name}"))
    )
    msg["From"] = smtp["from_email"]
    msg["To"] = delegate.email

    send_email(msg, content, smtp)


def send_email(msg, content, smtp):
    html = MIMEText(content, "html")
    msg.make_mixed()  # This converts the message to multipart/mixed
    msg.attach(html)

    connection_func = smtplib.SMTP_SSL if smtp["ssl"] else smtplib.SMTP
    with connection_func(smtp["host"], smtp["port"]) as smtp_connect:
        if smtp["starttls"]:
            smtp_connect.starttls()
        if smtp["username"]:
            smtp_connect.login(smtp["username"], smtp["password"])
        smtp_connect.send_message(msg)


def model_converter(model):
    """Create a Flask URL converter for database model instances."""

    class ModelConverter(BaseConverter):
        def __init__(self, *args, required=True, **kwargs):
            self.required = required
            super().__init__(self, *args, **kwargs)

        def to_url(self, instance):
            return str(instance.id)

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

    return EnumConverter


def check_oidc_connection(auth):
    """Ensure OIDC client connection is properly initialized."""

    def decorator_func(initial_func):
        @wraps(initial_func)
        def wrapper_func(*args, **kwargs):
            if not auth.clients:
                auth.clients = {
                    name: PyoidcFacade(
                        configuration, auth._redirect_uri_config.full_uri
                    )
                    for (name, configuration) in auth._provider_configurations.items()
                }
            return initial_func(*args, **kwargs)

        return wrapper_func

    return decorator_func


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
