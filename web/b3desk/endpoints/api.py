from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6750 import InvalidTokenError
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
from flask import Blueprint
from flask import current_app
from flask import request

from b3desk.models.meetings import get_or_create_shadow_meeting
from b3desk.models.users import get_or_create_user
from b3desk.utils import http_client

from .. import oauth

bp = Blueprint("api", __name__)

require_oauth = ResourceProtector()


class OIDCIntrospectTokenValidator(IntrospectTokenValidator):
    def introspect_token(self, token_string):
        introspection_endpoint = oauth.default.load_server_metadata()[
            "introspection_endpoint"
        ]
        response = http_client().post(
            introspection_endpoint,
            data={"token": token_string},
            auth=(
                current_app.config["OIDC_CLIENT_ID"],
                current_app.config["OIDC_CLIENT_SECRET"],
            ),
        )
        response.raise_for_status()
        return response.json()

    def validate_token(self, token, scopes, request):
        super().validate_token(token, scopes, request)
        audience = token.get("aud") or []
        if isinstance(audience, str):
            audience = [audience]
        if current_app.config["OIDC_CLIENT_ID"] not in audience:
            raise InvalidTokenError(realm=self.realm)


require_oauth.register_token_validator(OIDCIntrospectTokenValidator())


def _get_authenticated_user():
    """Fetch userinfo for the bearer token validated by require_oauth, and get or create the matching user."""
    access_token = request.headers["Authorization"].split(maxsplit=1)[1]
    userinfo = oauth.default.userinfo(
        token={"access_token": access_token, "token_type": "Bearer"}
    )
    return get_or_create_user(userinfo)


@bp.route("/api/meetings")
@require_oauth(["openid"])
def api_meetings():
    """Return all non-shadow meetings owned by or delegated to the authenticated user via API."""
    user = _get_authenticated_user()

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
@require_oauth(["openid"])
def shadow_meeting():
    """Get or create the shadow meeting for the authenticated user via API."""
    user = _get_authenticated_user()

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
