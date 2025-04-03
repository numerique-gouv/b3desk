from flask import Blueprint
from flask import current_app
from flask import request

from b3desk.models.meetings import create_and_save_shadow_meeting
from b3desk.models.roles import Role
from b3desk.models.users import get_or_create_user
from b3desk.utils import check_oidc_connection

from .. import auth

bp = Blueprint("api", __name__)


@bp.route("/api/meetings")
@check_oidc_connection(auth)
@auth.token_auth("default", scopes_required=["profile", "email"])
def api_meetings():
    client = auth.clients["default"]
    access_token = auth._parse_access_token(request)
    userinfo = client.userinfo_request(access_token).to_dict()
    user = get_or_create_user(userinfo)

    return {
        "meetings": [
            {
                **{
                    "name": meeting.name,
                    "moderator_url": meeting.get_signin_url(Role.moderator),
                    "attendee_url": meeting.get_signin_url(Role.attendee),
                },
                **(
                    {
                        "phone_number": current_app.config["BIGBLUEBUTTON_DIALNUMBER"],
                        "PIN": meeting.voiceBridge,
                    }
                    if current_app.config["ENABLE_PIN_MANAGEMENT"]
                    else {}
                ),
            }
            for meeting in user.meetings
            if not meeting.is_shadow_meeting
        ]
    }


@bp.route("/api/shadow-meeting")
@check_oidc_connection(auth)
@auth.token_auth("default", scopes_required=["profile", "email"])
def shadow_meeting():
    # avec cette route on récupère les liens vers le meeting
    # penser à changer le nom de cette route
    client = auth.clients["default"]
    access_token = auth._parse_access_token(request)
    userinfo = client.userinfo_request(access_token).to_dict()
    user = get_or_create_user(userinfo)
    meetings = [meeting for meeting in user.meetings if meeting.is_shadow_meeting]

    meeting = create_and_save_shadow_meeting(user) if not meetings else meetings[0]

    return {
        "shadow-meeting": [
            {
                "name": meeting.name,
                "moderator_url": meeting.get_signin_url(Role.moderator),
                "attendee_url": meeting.get_signin_url(Role.attendee),
            }
        ]
    }
