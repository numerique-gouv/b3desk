import random
from datetime import datetime

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import lazy_gettext as _

from b3desk.endpoints.captcha import captcha_validation
from b3desk.forms import JoinMailMeetingForm
from b3desk.forms import JoinMeetingForm
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import get_mail_meeting
from b3desk.models.meetings import get_meeting_by_visio_code
from b3desk.models.meetings import get_meeting_from_meeting_id_and_user_id
from b3desk.models.roles import Role
from b3desk.models.users import User
from b3desk.session import visio_code_attempt_counter_increment
from b3desk.session import visio_code_attempt_counter_reset
from b3desk.utils import check_oidc_connection
from b3desk.utils import check_token_errors

from .. import auth
from ..session import get_authenticated_attendee_fullname
from ..session import get_current_user
from ..session import has_user_session
from ..session import meeting_owner_needed
from ..session import should_display_captcha

bp = Blueprint("join", __name__)

SECONDS_BEFORE_REFRESH = 10
INCREASE_REFRESH_TIME = 1.5
MAXIMUM_REFRESH_TIME = 60


@bp.route(
    "/meeting/signinmail/<meeting_fake_id>/expiration/<expiration>/hash/<h>",
)
def signin_mail_meeting(meeting_fake_id, expiration, h):
    """Display the join form for quick meetings accessed via email link."""
    meeting = get_mail_meeting(meeting_fake_id)
    wordings = current_app.config["WORDINGS"]

    if meeting is None:
        flash(
            _(
                "Aucune %(meeting_label)s ne correspond à ces paramètres",
                meeting_label=wordings["meeting_label"],
            ),
            "success",
        )
        return redirect(url_for("public.index"))

    hash_matches = meeting.get_mail_signin_hash(meeting_fake_id, expiration) == h
    if not hash_matches:
        flash(_("Lien invalide"), "error")
        return redirect(url_for("public.index"))

    is_expired = datetime.fromtimestamp(float(expiration)) < datetime.now()
    if is_expired:
        flash(_("Lien expiré"), "error")
        return redirect(url_for("public.index"))

    return render_template(
        "meeting/signinmail.html",
        meeting=meeting,
        meeting_fake_id=meeting.fake_id,
        expiration=expiration,
        user_id=random.randint(100000, 999999),
        h=h,
        role=Role.moderator,
    )


@bp.route("/meeting/joinmail", methods=["POST"])
def join_mail_meeting():
    """Process the join form submission for email-accessed quick meetings."""
    form = JoinMailMeetingForm(request.form)
    if not form.validate():
        flash(_("Lien invalide"), "error")
        return redirect(url_for("public.index"))

    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    expiration = form["expiration"].data
    h = form["h"].data

    meeting = get_mail_meeting(meeting_fake_id)
    if meeting is None:
        flash(
            _(
                "%(meeting_label)s inexistante",
                meeting_label=current_app.config["WORDINGS"][
                    "meeting_label"
                ].capitalize(),
            ),
            "error",
        )
        return redirect(url_for("public.index"))

    hash_matches = meeting.get_mail_signin_hash(meeting_fake_id, expiration) == h
    if not hash_matches:
        flash(_("Lien invalide"), "error")
        return redirect(url_for("public.index"))

    is_expired = datetime.fromtimestamp(expiration) < datetime.now()
    if is_expired:
        flash(_("Lien expiré"), "error")
        return redirect(url_for("public.index"))

    created = meeting.create_bbb()
    return redirect(
        meeting.get_join_url(
            Role.moderator, fullname, quick_meeting=True, waiting_room=not created
        )
    )


# The role needs to appear in the URL, even if it is unused, so user won't
# mix up invitation links.
# https://github.com/numerique-gouv/b3desk/issues/93
@bp.route(
    "/meeting/signin/<role:role>/<meeting_fake_id>/creator/<user:creator>/hash/<h>"
)
@bp.route("/meeting/signin/<meeting_fake_id>/creator/<user:creator>/hash/<h>")
def signin_meeting(meeting_fake_id, creator: User, h, role: Role | None = None):
    """Get users in the meeting.

    - Unauthenticated users are display a name choosing form 'join.html'
    - Authenticated users are redirected to 'waiting_meeting'
    """
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, creator.id)
    wordings = current_app.config["WORDINGS"]
    if meeting is None:
        flash(
            _(
                "Aucune %(meeting_label)s ne correspond à ces paramètres",
                meeting_label=wordings["meeting_label"],
            ),
            "success",
        )
        return redirect(url_for("public.index"))

    current_user = get_current_user() if has_user_session() else None
    role = meeting.get_role(h, current_user)

    if role == Role.authenticated:
        return redirect(
            url_for("join.join_meeting_as_authenticated", meeting_id=meeting_fake_id)
        )
    elif not role:
        flash(_("Le lien d'invitation que vous avez utilisé est invalide."), "error")

        return redirect(url_for("public.index"))

    return render_template(
        "meeting/join.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        creator=creator,
        h=h,
        role=role,
    )


@bp.route("/meeting/auth/<meeting_fake_id>/creator/<user:creator>/hash/<h>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def authenticate_then_signin_meeting(meeting_fake_id, creator: User, h):
    """Authenticate user via OIDC then redirect to meeting signin page."""
    return redirect(
        url_for(
            "join.signin_meeting",
            meeting_fake_id=meeting_fake_id,
            creator=creator,
            h=h,
        )
    )


@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user:creator>/hash/<h>/fullname/fullname_suffix/",
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user:creator>/hash/<h>/fullname/<path:fullname>/fullname_suffix/",
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user:creator>/hash/<h>/fullname/fullname_suffix/<path:fullname_suffix>",
)
@bp.route(
    "/meeting/wait/<meeting_fake_id>/creator/<user:creator>/hash/<h>/fullname/<path:fullname>/fullname_suffix/<path:fullname_suffix>",
)
def waiting_meeting(meeting_fake_id, creator: User, h, fullname="", fullname_suffix=""):
    """Display a page until the BBB meeting is created.

    The page wait a few seconds, then redirect to 'join_meeting'.
    """
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, creator.id)
    if meeting is None:
        flash(_("Le lien d'invitation que vous avez utilisé est invalide."), "error")
        return redirect(url_for("public.index"))

    current_user = get_current_user() if has_user_session() else None
    role = meeting.get_role(h, current_user)
    if not role:
        flash(_("Le lien d'invitation que vous avez utilisé est invalide."), "error")
        return redirect(url_for("public.index"))
    seconds_before_refresh = request.args.get(
        "seconds_before_refresh", SECONDS_BEFORE_REFRESH
    )
    quick_meeting = request.args.get("quick_meeting", False)

    return render_template(
        "meeting/wait.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        creator=creator,
        h=h,
        role=role,
        fullname=fullname,
        fullname_suffix=fullname_suffix,
        seconds_before_refresh=seconds_before_refresh,
        quick_meeting=quick_meeting,
    )


@bp.route("/meeting/join", methods=["POST"])
def join_meeting():
    """Validate the form from wait.html and join.html.

    Then redirect to the BBB meeting if available, and back to the waiting room if not.
    """
    form = JoinMeetingForm(request.form)
    if not form.validate():
        flash(_("Lien invalide"), "error")
        return redirect(url_for("public.index"))

    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    user_id = form["user_id"].data
    h = form["h"].data
    seconds_before_refresh = None
    if (
        "seconds_before_refresh" in form
        and form["seconds_before_refresh"].data is not None
    ):
        seconds_before_refresh = min(
            form["seconds_before_refresh"].data * INCREASE_REFRESH_TIME,
            MAXIMUM_REFRESH_TIME,
        )

    quick_meeting = None
    if "quick_meeting" in form:
        quick_meeting = form["quick_meeting"].data
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    if meeting is None:
        flash(_("Le lien d'invitation que vous avez utilisé est invalide."), "error")
        return redirect(url_for("public.index"))

    current_user = get_current_user() if has_user_session() else None
    role = meeting.get_role(h, current_user)
    fullname_suffix = form["fullname_suffix"].data
    if role == Role.authenticated:
        fullname = get_authenticated_attendee_fullname()
    elif not role:
        flash(_("Le lien d'invitation que vous avez utilisé est invalide."), "error")
        return redirect(url_for("public.index"))

    if role == Role.moderator:
        created = meeting.create_bbb()
        waiting_room = not created
    else:
        waiting_room = True

    return redirect(
        meeting.get_join_url(
            role,
            fullname,
            fullname_suffix=fullname_suffix,
            seconds_before_refresh=seconds_before_refresh,
            quick_meeting=quick_meeting,
            waiting_room=waiting_room,
        )
    )


# Cannot use a flask converter here because sometimes 'meeting_id' is a 'fake_id'
@bp.route("/meeting/join/<int:meeting_id>/authenticated")
@check_oidc_connection(auth)
@auth.oidc_auth("attendee")
def join_meeting_as_authenticated(meeting_id):
    """Join a meeting with authenticated attendee role using OIDC."""
    # TODO: Not sure this endpoint is really useful as it is only called in 'signin_meeting'.
    # We should look if we can delete it.
    meeting = db.session.get(Meeting, meeting_id) or abort(404)
    role = Role.authenticated
    fullname = get_authenticated_attendee_fullname()
    return redirect(
        url_for(
            "join.waiting_meeting",
            meeting_fake_id=meeting_id,
            creator=meeting.user,
            h=meeting.get_hash(role),
            fullname=fullname,
        )
    )


@bp.route("/meeting/join/<meeting:meeting>/<role:role>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def join_meeting_as_role(meeting: Meeting, role: Role, owner: User):
    """Join a meeting as the owner with a specific role."""
    if role == Role.moderator:
        created = meeting.create_bbb()
        waiting_room = not created
    else:
        waiting_room = True
    return redirect(
        meeting.get_join_url(
            role,
            owner.fullname,
            waiting_room=waiting_room,
        )
    )


@bp.route("/sip-connect/<visio_code>", methods=["GET"])
@check_oidc_connection(auth)
def join_waiting_meeting_from_sip(visio_code):
    """Join a meeting using visio code from SIP phone connection."""
    token = request.headers.get("Authorization")
    if not check_token_errors(token):
        meeting = get_meeting_by_visio_code(visio_code)
        if not meeting:
            current_app.logger.error(
                "SQLAlchemy cannot find a meeting with this visio-code"
            )
            abort(404)
        return join_waiting_meeting_with_visio_code(meeting)
    abort(401)


@bp.route("/meeting/visio_code", methods=["POST"])
@check_oidc_connection(auth)
def visio_code_connection():
    """Process visio code form submission and redirect to meeting if valid."""
    visio_code = (
        request.form.get("visio_code1")
        + request.form.get("visio_code2")
        + request.form.get("visio_code3")
    )

    if should_display_captcha(check_service_status=False):
        captcha_uuid = request.form.get("captchetat-uuid")
        captcha_code = request.form.get("captchaCode")
        if not captcha_validation(captcha_uuid, captcha_code):
            flash(_("Le captcha saisi est erroné"), "error")
            return redirect(url_for("public.home"))

    meeting = get_meeting_by_visio_code(visio_code)
    if not meeting:
        flash(_("Le code de connexion saisi est erroné"), "error")
        visio_code_attempt_counter_increment()
        return redirect(url_for("public.home"))

    visio_code_attempt_counter_reset()
    return join_waiting_meeting_with_visio_code(meeting)


@bp.route("/meeting/visio_code_form", methods=["POST"])
@check_oidc_connection(auth)
def visio_code_form_validation():
    """Validate the visio-code from from the front."""
    visio_code = (
        request.form.get("visio_code1")
        + request.form.get("visio_code2")
        + request.form.get("visio_code3")
    )
    meeting_exists = bool(get_meeting_by_visio_code(visio_code))
    if not meeting_exists:
        visio_code_attempt_counter_increment()

    result = {
        "visioCode": meeting_exists,
        "shouldDisplayCaptcha": should_display_captcha(check_service_status=False),
    }

    captcha_uuid = request.form.get("captchetat-uuid")
    captcha_code = request.form.get("captchaCode")
    if captcha_code:
        result["captchaCode"] = captcha_validation(captcha_uuid, captcha_code)

    return result


def join_waiting_meeting_with_visio_code(meeting):
    """Redirect to the meeting signin page after successful visio code validation."""
    meeting_fake_id = str(meeting.id)
    creator = db.session.get(User, meeting.user_id)
    role = Role.moderator
    h = meeting.get_hash(role=role)
    return signin_meeting(
        meeting_fake_id=meeting_fake_id, creator=creator, h=h, role=role
    )
