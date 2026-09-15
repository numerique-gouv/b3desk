from urllib.parse import urlencode

import requests
from authlib.integrations.base_client import MismatchingStateError
from authlib.integrations.base_client import OAuthError
from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_babel import lazy_gettext as _

from .. import cache
from .. import oauth
from ..session import clear_userinfo
from ..session import has_user_session
from ..session import login_required
from ..session import should_display_captcha
from ..session import store_attendee_userinfo
from ..session import store_userinfo
from ..templates.content import FAQ_CONTENT
from ..utils import check_private_key
from .meetings import meeting_mailto_params

bp = Blueprint("public", __name__)


@cache.cached(
    timeout=current_app.config["STATS_CACHE_DURATION"], key_prefix="meetings_stats"
)
def get_meetings_stats():
    """Retrieve current meeting statistics from the configured stats URL."""
    # TODO: do this asynchroneously
    # Currently, the page needs to wait another network request in get_meetings_stats
    # before it can be rendered. This is mitigated by caching though.

    if not current_app.config["STATS_URL"]:
        return None

    try:
        response = requests.get(current_app.config["STATS_URL"])
        if response.status_code != 200:
            return None
        stats_array = response.content.decode(encoding="utf-8").split("\n")
        stats_array = [row.split(",") for row in stats_array]
        participant_count = int(stats_array[current_app.config["STATS_INDEX"]][1])
        running_count = int(stats_array[current_app.config["STATS_INDEX"]][2])
    except requests.RequestException:
        return None

    return {"participantCount": participant_count, "runningCount": running_count}


@bp.route("/")
def index():
    """Redirect to welcome page if authenticated, otherwise to home page."""
    if has_user_session():
        return redirect(url_for("public.welcome"))
    return redirect(url_for("public.home"))


@bp.route("/login")
def login():
    redirect_uri = url_for("public.authorize", _external=True)
    return oauth.default.authorize_redirect(redirect_uri)


@bp.route("/authorize")
def authorize():
    try:
        token = oauth.default.authorize_access_token()
    except MismatchingStateError as exc:
        current_app.logger.warning("OIDC authorization state mismatch: %s", exc)
        flash(_("Votre session de connexion a expiré, merci de réessayer."), "error")
        return redirect(url_for("public.home"))
    except OAuthError as exc:
        current_app.logger.warning("OIDC authorization error: %s", exc)
        flash(_("La connexion a été annulée."), "error")
        return redirect(url_for("public.home"))

    store_userinfo(token)
    return redirect(url_for("public.welcome"))


@bp.route(
    "/oidc_callback"
)  # vérifier ce qui est enregistré en prod dans OIDC_REDIRECT_URI
def attendee_callback():
    try:
        token = oauth.attendee.authorize_access_token()
    except MismatchingStateError as exc:
        current_app.logger.warning("Attendee OIDC state mismatch: %s", exc)
        flash(_("Votre session de connexion a expiré, merci de réessayer."), "error")
        return redirect(url_for("public.index"))
    except OAuthError as exc:
        current_app.logger.warning("Attendee OIDC authorization error: %s", exc)
        flash(_("La connexion a été annulée."), "error")
        return redirect(url_for("public.index"))

    store_attendee_userinfo(token)
    meeting_id = session.pop("attendee_next_meeting_id", None) or abort(404)
    return redirect(
        url_for("join.join_meeting_as_authenticated", meeting_id=meeting_id)
    )


@bp.route("/home")
@check_private_key()
def home():
    """Render the public home page for unauthenticated users."""
    if has_user_session():
        return redirect(url_for("public.welcome"))

    stats = get_meetings_stats()
    return render_template(
        "index.html",
        stats=stats,
        max_participants=current_app.config["MAX_PARTICIPANTS"],
        should_display_captcha=should_display_captcha(),
    )


@bp.route("/welcome")
@login_required
@check_private_key()
def welcome():
    """Render the authenticated user's welcome page with their meetings."""
    stats = get_meetings_stats()

    order_key = request.args.get("order_key", "created_at")
    reverse_order = request.args.get(
        "reverse_order", True, type=lambda x: x.lower() == "true"
    )
    favorite_filter = request.args.get(
        "favorite_filter", False, type=lambda x: x.lower() == "true"
    )

    if order_key not in ["created_at", "name"]:
        order_key = "created_at"

    meetings = [meeting for meeting in g.user.meetings if not meeting.is_shadow] + [
        meeting for meeting in g.user.get_all_delegated_meetings
    ]
    favorite_meetings = []
    if favorite_filter:
        favorite_meetings = [
            meeting for meeting in meetings if g.user in meeting.favorite_of
        ]
        if favorite_meetings:
            meetings = favorite_meetings

    meetings = sorted(
        meetings,
        key=lambda m: (
            getattr(m, order_key).lower()
            if isinstance(getattr(m, order_key), str)
            else getattr(m, order_key),
            m.created_at,
        ),
        reverse=reverse_order,
    )

    return render_template(
        "welcome.html",
        stats=stats,
        max_participants=current_app.config["MAX_PARTICIPANTS"],
        can_create_meetings=g.user.can_create_meetings,
        max_meetings_per_user=current_app.config["MAX_MEETINGS_PER_USER"],
        meeting_mailto_params=meeting_mailto_params,
        mailto=current_app.config["MAILTO_LINKS"],
        quick_meeting=current_app.config["QUICK_MEETING"],
        clipboard=current_app.config["CLIPBOARD"],
        meetings=meetings,
        reverse_order=reverse_order,
        order_key=order_key,
        favorite_filter=favorite_filter and bool(favorite_meetings),
        should_display_captcha=should_display_captcha(),
        admin_mode=False,
    )


@bp.route("/mentions_legales")
def mentions_legales():
    """Render the legal notices page."""
    return render_template(
        "footer/mentions_legales.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/cgu")
def cgu():
    """Render the terms of service page."""
    return render_template(
        "footer/cgu.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/donnees_personnelles")
def donnees_personnelles():
    """Render the personal data policy page."""
    return render_template(
        "footer/donnees_personnelles.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/accessibilite")
def accessibilite():
    """Render the accessibility statement page."""
    return render_template(
        "footer/accessibilite.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/documentation")
def documentation():
    """Redirect to external documentation or render internal documentation page."""
    if current_app.config["DOCUMENTATION_LINK"]["is_external"]:
        return redirect(current_app.config["DOCUMENTATION_LINK"]["url"])
    return render_template(
        "footer/documentation.html",
    )


@bp.route("/logout")
def logout():
    """Log out the current user locally, and from the OIDC provider if it supports it."""
    id_token = session.get("id_token")
    clear_userinfo()

    end_session_endpoint = oauth.default.load_server_metadata().get(
        "end_session_endpoint"
    )
    if end_session_endpoint and id_token:
        params = {
            "id_token_hint": id_token,
            "post_logout_redirect_uri": url_for("public.logout", _external=True),
        }
        return redirect(f"{end_session_endpoint}?{urlencode(params)}")

    return redirect(url_for("public.index"))


@bp.route("/faq")
def faq():
    """Render the frequently asked questions page."""
    return render_template(
        "faq.html",
        contents=FAQ_CONTENT,
    )
