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
from joserfc.errors import BadSignatureError
from joserfc.errors import InvalidClaimError
from joserfc.jwk import RSAKey
from joserfc.jwt import JWTClaimsRegistry
from joserfc.jwt import decode

from b3desk.forms import JoinMailMeetingForm
from b3desk.forms import JoinMeetingForm
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import get_mail_meeting
from b3desk.models.meetings import get_meeting_from_meeting_id_and_user_id
from b3desk.models.roles import Role
from b3desk.models.users import User
from b3desk.utils import check_oidc_connection

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
        role=Role.moderator,
    )


# The role needs to appear in the URL, even if it is unused, so user won't
# mix up invitation links.
# https://github.com/numerique-gouv/b3desk/issues/93
@bp.route(
    "/meeting/signin/<role:role>/<meeting_fake_id>/creator/<user:creator>/hash/<h>"
)
@bp.route("/meeting/signin/<meeting_fake_id>/creator/<user:creator>/hash/<h>")
def signin_meeting(meeting_fake_id, creator: User, h, role: Role = None):
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

    if role == Role.authenticated:
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
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def authenticate_then_signin_meeting(meeting_fake_id, creator: User, h):
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
    if role == Role.authenticated:
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

    return redirect(meeting.get_join_url(Role.moderator, fullname, create=True))


# Cannot use a flask converter here because sometimes 'meeting_id' is a 'fake_id'
@bp.route("/meeting/join/<int:meeting_id>/authenticated")
@check_oidc_connection(auth)
@auth.oidc_auth("attendee")
def join_meeting_as_authenticated(meeting_id):
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
    return redirect(meeting.get_join_url(role, owner.fullname, create=True))


@bp.route("/sip-connect/<visio_code>", methods=["GET"])
@check_oidc_connection(auth)
def join_waiting_meeting_from_sip(visio_code):
    token = request.headers.get("Authorization")
    if token is None:
        current_app.logger.error("SIP request has no token")
        abort(401)
    else:
        private_key_from_settings = RSAKey.import_key(current_app.config["PRIVATE_KEY"])
        public_key = private_key_from_settings.as_dict(private=False)
        public_key_obj = RSAKey.import_key(public_key)
        try:
            decoded_token = decode(token, public_key_obj)
            claims_requests = JWTClaimsRegistry(
                iss={
                    "value": f"{current_app.config['PREFERRED_URL_SCHEME']}://{current_app.config['SERVER_NAME']}"
                }
            )
            claims_requests.validate(decoded_token.claims)
        except BadSignatureError as err:
            current_app.logger.error(
                "The token is not recognized by the private key: %s", err
            )
            abort(401)
        except InvalidClaimError as err:
            current_app.logger.error(
                "The token was not generated by this instance of B3Desk: %s://%s, %s",
                current_app.config["PREFERRED_URL_SCHEME"],
                current_app.config["SERVER_NAME"],
                err,
            )
            abort(401)

        meeting = Meeting.query.filter_by(visio_code=visio_code).one_or_none()
        if not meeting:
            current_app.logger.error(
                "SQLAlchemy cannot find a meeting with this visio-code"
            )
            abort(404)
        meeting_fake_id = str(meeting.id)
        creator = User.query.filter_by(id=meeting.user_id).one()
        role = Role.moderator
        h = meeting.get_hash(role=role)
        return signin_meeting(
            meeting_fake_id=meeting_fake_id, creator=creator, h=h, role=role
        )
