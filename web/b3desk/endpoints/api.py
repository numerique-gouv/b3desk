from flask import Blueprint
from flask import current_app
from flask import request

from b3desk.models.meetings import get_or_create_shadow_meeting
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
                **(
                    {
                        "visio_code": meeting.visio_code,
                        "SIPMediaGW_url": meeting.visio_code
                        + "@"
                        + current_app.config["FQDN_SIP_SERVER"],
                    }
                    if current_app.config["ENABLE_VISIO_CODE"]
                    else {}
                ),
            }
            for meeting in user.meetings
            if not meeting.is_shadow
        ]
    }


@bp.route("/api/shadow-meeting")
@check_oidc_connection(auth)
@auth.token_auth("default", scopes_required=["profile", "email"])
def shadow_meeting():
    client = auth.clients["default"]
    access_token = auth._parse_access_token(request)
    userinfo = client.userinfo_request(access_token).to_dict()
    user = get_or_create_user(userinfo)

    meeting = get_or_create_shadow_meeting(user)

    return {
        "shadow-meeting": [
            {
                **{
                    "name": meeting.name,
                    "moderator_url": meeting.get_signin_url(Role.moderator),
                    "attendee_url": meeting.get_signin_url(Role.attendee),
                },
                **(
                    {
                        "visio_code": meeting.visio_code,
                        "SIPMediaGW_url": meeting.visio_code
                        + "@"
                        + current_app.config["FQDN_SIP_SERVER"],
                    }
                    if current_app.config["ENABLE_VISIO_CODE"]
                    else {}
                ),
            }
        ]
    }
