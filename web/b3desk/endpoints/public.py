import requests
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from .. import auth
from .. import cache
from ..session import get_current_user
from ..session import has_user_session
from ..templates.content import FAQ_CONTENT
from .meetings import meeting_mailto_params

bp = Blueprint("public", __name__)


@cache.cached(
    timeout=current_app.config["STATS_CACHE_DURATION"], key_prefix="meetings_stats"
)
def get_meetings_stats():
    # TODO: do this asynchroneously
    # Currently, the page needs to wait another network request in get_meetings_stats
    # before it can be rendered. This is mitigated by caching though.

    if not current_app.config["STATS_URL"]:
        return None

    response = requests.get(current_app.config["STATS_URL"])
    if response.status_code != 200:
        return None

    try:
        stats_array = response.content.decode(encoding="utf-8").split("\n")
        stats_array = [row.split(",") for row in stats_array]
        participant_count = int(stats_array[current_app.config["STATS_INDEX"]][1])
        running_count = int(stats_array[current_app.config["STATS_INDEX"]][2])
    except Exception:
        return None

    result = {"participantCount": participant_count, "runningCount": running_count}
    return result


@bp.route("/")
def index():
    if has_user_session():
        return redirect(url_for("public.welcome"))
    else:
        return redirect(url_for("public.home"))


@bp.route("/home")
def home():
    if has_user_session():
        return redirect(url_for("public.welcome"))

    stats = get_meetings_stats()
    return render_template(
        "index.html",
        stats=stats,
        mail_meeting=current_app.config["MAIL_MEETING"],
        max_participants=current_app.config["MAX_PARTICIPANTS"],
    )


@bp.route("/welcome")
@auth.oidc_auth("default")
def welcome():
    user = get_current_user()
    stats = get_meetings_stats()

    order_key = request.args.get("order-key", "created_at")
    reverse_order = request.args.get("reverse-order", "true")
    favorite = request.args.get("favorite", "false")
    
    if order_key not in ["created_at", "name"]:
        order_key = "created_at"
    if reverse_order == "false":
        reverse_order = False
    else:
        reverse_order = True
    
    favorite_meetings = [meeting for meeting in user.meetings if meeting.favorite]
        
    if favorite == "true" and favorite_meetings:
        favorite = True
    else:
        favorite = False
    
    
    meetings = sorted(favorite_meetings if favorite else user.meetings, key=lambda m: (getattr(m, order_key).lower() if isinstance(getattr(m, order_key), str) else getattr(m, order_key), m.id), reverse=reverse_order)
    
    return render_template(
        "welcome.html",
        stats=stats,
        max_participants=current_app.config["MAX_PARTICIPANTS"],
        can_create_meetings=user.can_create_meetings,
        max_meetings_per_user=current_app.config["MAX_MEETINGS_PER_USER"],
        meeting_mailto_params=meeting_mailto_params,
        mailto=current_app.config["MAILTO_LINKS"],
        quick_meeting=current_app.config["QUICK_MEETING"],
        file_sharing=current_app.config["FILE_SHARING"],
        clipboard=current_app.config["CLIPBOARD"],
        meetings=meetings,
        reverse_order=reverse_order,
        order_key=order_key,
        favorite=favorite,
    )


@bp.route("/mentions_legales")
def mentions_legales():
    return render_template(
        "footer/mentions_legales.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/cgu")
def cgu():
    return render_template(
        "footer/cgu.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/donnees_personnelles")
def donnees_personnelles():
    return render_template(
        "footer/donnees_personnelles.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/accessibilite")
def accessibilite():
    return render_template(
        "footer/accessibilite.html",
        service_title=current_app.config["SERVICE_TITLE"],
        service_tagline=current_app.config["SERVICE_TAGLINE"],
    )


@bp.route("/documentation")
def documentation():
    if current_app.config["DOCUMENTATION_LINK"]["is_external"]:
        return redirect(current_app.config["DOCUMENTATION_LINK"]["url"])
    return render_template(
        "footer/documentation.html",
    )


@bp.route("/logout")
@auth.oidc_logout
def logout():
    return redirect(url_for("public.index"))


@bp.route("/faq")
def faq():
    return render_template(
        "faq.html",
        contents=FAQ_CONTENT,
    )
