from flask import Blueprint
from flask import current_app
from flask import request

from b3desk.models.meetings import get_or_create_shadow_meeting
from b3desk.models.users import get_or_create_user
from b3desk.utils import check_oidc_connection

from .. import auth

bp = Blueprint("api", __name__)


@bp.route("/api/meetings")
@check_oidc_connection(auth)
@auth.token_auth("default", scopes_required=["openid"])
def api_meetings():
    """Return all non-shadow meetings owned by or delegated to the authenticated user via API."""
    client = auth.clients["default"]
    access_token = auth._parse_access_token(request)
    userinfo = client.userinfo_request(access_token).to_dict()
    user = get_or_create_user(userinfo)

    owned = [(meeting, False) for meeting in user.meetings if not meeting.is_shadow]
    delegated = [(meeting, True) for meeting in user.get_all_delegated_meetings]

    return {
        "meetings": [
            {
                "name": meeting.name,
                "moderator_url": meeting.moderator_url,
                "attendee_url": meeting.attendee_url,
                "visio_code": meeting.visio_code,
                "delegate": is_delegate,
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
                        "SIPMediaGW_url": meeting.visio_code
                        + "@"
                        + current_app.config["FQDN_SIP_SERVER"],
                    }
                    if meeting.owner.can_use_sip
                    else {}
                ),
            }
            for meeting, is_delegate in owned + delegated
        ]
    }


@bp.route("/api/shadow-meeting")
@check_oidc_connection(auth)
@auth.token_auth("default", scopes_required=["openid"])
def shadow_meeting():
    """Get or create the shadow meeting for the authenticated user via API."""
    client = auth.clients["default"]
    access_token = auth._parse_access_token(request)
    userinfo = client.userinfo_request(access_token).to_dict()
    user = get_or_create_user(userinfo)

    meeting = get_or_create_shadow_meeting(user)

    return {
        "shadow-meeting": [
            {
                "name": meeting.name,
                "moderator_url": meeting.moderator_url,
                "attendee_url": meeting.attendee_url,
                "visio_code": meeting.visio_code,
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
                        "SIPMediaGW_url": meeting.visio_code
                        + "@"
                        + current_app.config["FQDN_SIP_SERVER"],
                    }
                    if meeting.owner.can_use_sip
                    else {}
                ),
            }
        ]
    }
