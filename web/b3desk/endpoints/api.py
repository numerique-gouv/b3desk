from b3desk.models.users import get_or_create_user
from flask import Blueprint
from flask import request

from .. import auth


bp = Blueprint("api", __name__)


@bp.route("/api/meetings")
@auth.token_auth("default", scopes_required=["profile", "email"])
def api_meetings():
    client = auth.clients["default"]
    access_token = auth._parse_access_token(request)
    userinfo = client.userinfo_request(access_token).to_dict()
    user = get_or_create_user(userinfo)

    return {
        "meetings": [
            {
                "name": m.name,
                "moderator_url": m.get_signin_url("moderator"),
                "attendee_url": m.get_signin_url("attendee"),
            }
            for m in user.meetings
        ]
    }