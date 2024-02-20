import random
import re
import smtplib
import string
from email.message import EmailMessage
from email.mime.text import MIMEText

from b3desk.models import db
from flask import abort
from flask import current_app
from flask import render_template
from flask import request
from netaddr import IPAddress
from netaddr import IPNetwork
from werkzeug.routing import BaseConverter


def secret_key():
    return current_app.config["SECRET_KEY"]


def is_rie():
    """Checks wether the request was made from inside the state network "Réseau
    Interministériel de l’État"."""
    if not request.remote_addr:
        return False

    return current_app.config["RIE_NETWORK_IPS"] and any(
        IPAddress(request.remote_addr) in IPNetwork(str(network_ip))
        for network_ip in current_app.config["RIE_NETWORK_IPS"]
        if network_ip
    )


def is_accepted_email(email):
    for regex in current_app.config["EMAIL_WHITELIST"]:
        if re.search(regex, email):
            return True
    return False


def is_valid_email(email):
    if not email or not re.search(
        r"^([a-zA-Z0-9_\-\.']+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$", email
    ):
        return False
    return True


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = "".join(random.choice(letters_and_digits) for i in range(length))
    return result_str


def send_mail(meeting, to_email):
    smtp_from = current_app.config["SMTP_FROM"]
    smtp_host = current_app.config["SMTP_HOST"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_ssl = current_app.config["SMTP_SSL"]
    smtp_username = current_app.config["SMTP_USERNAME"]
    smtp_password = current_app.config["SMTP_PASSWORD"]
    wordings = current_app.config["WORDINGS"]
    msg = EmailMessage()
    content = render_template(
        "meeting/mailto/mail_quick_meeting_body.txt",
        role="moderator",
        moderator_mail_signin_url=meeting.get_mail_signin_url(),
        welcome_url=current_app.config["SERVER_FQDN"] + "/welcome",
        meeting=meeting,
    )
    msg["Subject"] = wordings["meeting_mail_subject"]
    msg["From"] = smtp_from
    msg["To"] = to_email
    html = MIMEText(content, "html")
    msg.make_mixed()  # This converts the message to multipart/mixed
    msg.attach(html)

    if smtp_ssl:
        s = smtplib.SMTP_SSL(smtp_host, smtp_port)
    else:
        s = smtplib.SMTP(smtp_host, smtp_port)
    if smtp_username:
        # in dev, no need for username
        s.login(smtp_username, smtp_password)
    s.send_message(msg)
    s.quit()


def model_converter(model):
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
