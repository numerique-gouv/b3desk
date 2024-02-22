from datetime import datetime

from b3desk.forms import JoinMailMeetingForm
from b3desk.forms import JoinMeetingForm
from b3desk.models import db
from b3desk.models.meetings import get_mail_meeting
from b3desk.models.meetings import get_meeting_from_meeting_id_and_user_id
from b3desk.models.meetings import Meeting
from flask import abort
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import lazy_gettext as _

from .. import auth
from ..session import get_authenticated_attendee_fullname
from ..session import get_current_user
from ..session import has_user_session
from ..session import meeting_owner_needed


bp = Blueprint("join", __name__)


@bp.route(
    "/meeting/signinmail/<meeting_fake_id>/expiration/<expiration>/hash/<h>",
)
def signin_mail_meeting(meeting_fake_id, expiration, h):
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
        "meeting/joinmail.html",
        meeting=meeting,
        meeting_fake_id=meeting.fake_id,
        expiration=expiration,
        user_id="fakeuserId",
        h=h,
        role="moderator",
    )


@bp.route("/meeting/signin/<meeting_fake_id>/creator/<user:creator>/hash/<h>")
def signin_meeting(meeting_fake_id, creator, h):
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

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)

    if role == "authenticated":
        return redirect(
            url_for("join.join_meeting_as_authenticated", meeting_id=meeting_fake_id)
        )
    elif not role:
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
@auth.oidc_auth("default")
def authenticate_then_signin_meeting(meeting_fake_id, creator, h):
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
def waiting_meeting(meeting_fake_id, creator, h, fullname="", fullname_suffix=""):
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, creator.id)
    if meeting is None:
        return redirect(url_for("public.index"))

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)
    if not role:
        return redirect(url_for("public.index"))

    return render_template(
        "meeting/wait.html",
        meeting=meeting,
        meeting_fake_id=meeting_fake_id,
        creator=creator,
        h=h,
        role=role,
        fullname=fullname,
        fullname_suffix=fullname_suffix,
    )


@bp.route("/meeting/join", methods=["POST"])
def join_meeting():
    form = JoinMeetingForm(request.form)
    if not form.validate():
        return redirect(url_for("public.index"))

    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    user_id = form["user_id"].data
    h = form["h"].data
    meeting = get_meeting_from_meeting_id_and_user_id(meeting_fake_id, user_id)
    if meeting is None:
        return redirect(url_for("public.index"))

    current_user_id = get_current_user().id if has_user_session() else None
    role = meeting.get_role(h, current_user_id)
    fullname_suffix = form["fullname_suffix"].data
    if role == "authenticated":
        fullname = get_authenticated_attendee_fullname()
    elif not role:
        return redirect(url_for("public.index"))

    return redirect(
        meeting.get_join_url(
            role, fullname, fullname_suffix=fullname_suffix, create=True
        )
    )


@bp.route("/meeting/joinmail", methods=["POST"])
def join_mail_meeting():
    form = JoinMailMeetingForm(request.form)
    if not form.validate():
        flash("Lien invalide", "error")
        return redirect(url_for("public.index"))

    fullname = form["fullname"].data
    meeting_fake_id = form["meeting_fake_id"].data
    form["user_id"].data
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

    return redirect(meeting.get_join_url("moderator", fullname, create=True))


# Cannot use a flask converter here because sometimes 'meeting_id' is a 'fake_id'
@bp.route("/meeting/join/<int:meeting_id>/authenticated")
@auth.oidc_auth("attendee")
def join_meeting_as_authenticated(meeting_id):
    meeting = db.session.get(Meeting, meeting_id) or abort(404)
    role = "authenticated"
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


@bp.route("/meeting/join/<meeting:meeting>/<role>")
@auth.oidc_auth("default")
@meeting_owner_needed
def join_meeting_as_role(meeting, role, owner):
    if role not in ("attendee", "moderator"):
        abort(404)

    return redirect(meeting.get_join_url(role, owner.fullname, create=True))
