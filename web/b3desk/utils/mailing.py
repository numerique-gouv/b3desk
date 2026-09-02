import smtplib
from datetime import datetime
from email.message import EmailMessage

from flask import current_app
from flask import render_template
from flask import url_for
from flask_babel import format_datetime
from flask_babel import lazy_gettext as _

DELAY_FOR_FIRST_EMAIL = 30
DELAY_FOR_SECOND_EMAIL = 15
DELAY_FOR_THIRD_EMAIL = 1


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
        _("Nouvelle délégation pour {meeting_name}").format(meeting_name=meeting.name)
        if new_delegation
        else _("Retrait de délégation pour {meeting_name}").format(
            meeting_name=meeting.name
        )
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


def send_mail_before_meeting_deletion(meeting, delay):
    """Send email to inform the owner that the meeting will be deleted in `delay` days."""
    smtp = make_smtp()
    msg = EmailMessage()
    body_file = "mail_before_meeting_deletion"
    context = {
        "meeting": meeting,
        "delay": delay,
        "welcome_url": url_for("public.welcome", _external=True),
    }
    text = render_template(f"meeting/mailto/{body_file}.txt", **context)
    html = render_template(f"meeting/mailto/{body_file}.html", **context)
    msg["Subject"] = _("Information avant suppression : {meeting_name}").format(
        meeting_name=meeting.name
    )
    msg["From"] = smtp["from_email"]
    msg["To"] = meeting.owner.email

    send_email(msg, text, html, smtp)


def send_mail_before_user_deletion(user, delay):
    """Send email to inform the user that his account will be deleted in `delay` days."""
    smtp = make_smtp()
    msg = EmailMessage()
    body_file = "mail_before_user_account_deletion"
    context = {
        "user": user,
        "delay": delay,
        "welcome_url": url_for("public.welcome", _external=True),
    }
    text = render_template(f"meeting/mailto/{body_file}.txt", **context)
    html = render_template(f"meeting/mailto/{body_file}.html", **context)
    msg["Subject"] = str(_(f"Information avant suppression : {user.fullname}"))
    msg["From"] = smtp["from_email"]
    msg["To"] = user.email

    send_email(msg, text, html, smtp)


def send_email(msg, text, html, smtp):
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    connection_func = smtplib.SMTP_SSL if smtp["ssl"] else smtplib.SMTP
    try:
        with connection_func(smtp["host"], smtp["port"]) as smtp_connect:
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
