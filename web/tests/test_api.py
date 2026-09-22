import datetime

import pytest
from authlib.oauth2.rfc6750 import InvalidTokenError
from b3desk.endpoints.api import OIDCIntrospectTokenValidator
from b3desk.models import db
from b3desk.models.meetings import Meeting


def test_api_meetings_nominal(
    client_app,
    user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    iam_token,
):
    """Test that API returns meetings list with correct format."""
    attendee_url = meeting.attendee_url
    moderator_url = meeting.moderator_url

    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )
    assert res.json["meetings"][0]["name"] == "meeting"
    assert res.json["meetings"][1]["name"] == "a meeting"
    assert res.json["meetings"][2]["name"] == "meeting"
    assert res.json["meetings"][0] == {
        "PIN": "111111111",
        "attendee_url": attendee_url,
        "moderator_url": moderator_url,
        "name": "meeting",
        "phone_number": "+33bbbphonenumber",
        "visio_code": "911111111",
        "SIPMediaGW_url": "911111111@sip.test",
        "delegate": False,
    }
    assert len(res.json["meetings"]) == 3

    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = False
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )

    assert res.json["meetings"][0] == {
        "attendee_url": attendee_url,
        "moderator_url": moderator_url,
        "name": "meeting",
        "visio_code": "911111111",
        "SIPMediaGW_url": "911111111@sip.test",
        "delegate": False,
    }
    assert len(res.json["meetings"]) == 3

    client_app.app.config["ENABLE_SIP"] = False
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )

    assert res.json["meetings"][0] == {
        "attendee_url": attendee_url,
        "moderator_url": moderator_url,
        "name": "meeting",
        "visio_code": "911111111",
        "delegate": False,
    }
    assert len(res.json["meetings"]) == 3


def test_api_meetings_includes_delegated(
    client_app,
    user,
    meeting,
    meeting_1_user_2,
    iam_token,
):
    """Delegated meetings are returned by the API with delegate set to True."""
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )

    meetings_by_name = {item["name"]: item for item in res.json["meetings"]}
    assert "meeting" in meetings_by_name
    assert "delegated meeting" in meetings_by_name
    assert meetings_by_name["meeting"]["delegate"] is False
    assert meetings_by_name["delegated meeting"]["delegate"] is True


def test_api_meetings_no_token(client_app):
    """Test that API returns 401 without authentication token."""
    client_app.get("/api/meetings", status=401)


def test_api_meetings_invalid_token(client_app):
    """Test that API returns 401 with invalid authentication token."""
    client_app.get(
        "/api/meetings", headers={"Authorization": "Bearer invalid-token"}, status=401
    )


def test_api_meetings_token_expired(client_app, iam_server, iam_client, iam_user, user):
    """Test that API returns 401 with expired authentication token."""
    iam_token = iam_server.random_token(
        client=iam_client,
        subject=iam_user,
        issue_date=datetime.datetime(2000, 1, 1, tzinfo=datetime.UTC),
    )

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=401,
    )

    iam_server.backend.delete(iam_token)


def test_api_meetings_client_id_missing_in_token_audience(
    client_app, iam_server, iam_client, iam_user, user
):
    """Test that API returns 401 when client ID is missing in token audience."""
    iam_token = iam_server.random_token(
        client=iam_client,
        subject=iam_user,
        audience=[],
    )

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=401,
    )

    iam_server.backend.delete(iam_token)


def test_keycloak_introspect_token_validator_rejects_wrong_audience(client_app):
    """The audience check must be exercised directly here, not through the API.

    The canaille test server refuses to introspect a token whose audience
    doesn't include the requesting client (see
    test_api_meetings_client_id_missing_in_token_audience above), so this
    custom check can't be reached through a real HTTP call in tests.
    """
    validator = OIDCIntrospectTokenValidator()
    token = {"active": True, "aud": ["some-other-client"], "scope": "openid"}

    with client_app.app.app_context(), pytest.raises(InvalidTokenError):
        validator.validate_token(token, ["openid"], request=None)


def test_keycloak_introspect_token_validator_accepts_matching_audience(client_app):
    """A token whose audience includes our client_id and has the required scope is accepted."""
    validator = OIDCIntrospectTokenValidator()

    with client_app.app.app_context():
        token = {
            "active": True,
            "aud": [client_app.app.config["OIDC_CLIENT_ID"]],
            "scope": "openid",
        }
        validator.validate_token(token, ["openid"], request=None)


def test_keycloak_introspect_token_validator_accepts_matching_string_audience(
    client_app,
):
    """Some providers return a single audience as a bare string rather than a list."""
    validator = OIDCIntrospectTokenValidator()

    with client_app.app.app_context():
        token = {
            "active": True,
            "aud": client_app.app.config["OIDC_CLIENT_ID"],
            "scope": "openid",
        }
        validator.validate_token(token, ["openid"], request=None)


def test_keycloak_introspect_token_validator_rejects_wrong_string_audience(
    client_app,
):
    """A bare-string audience that doesn't match our client_id must be rejected too."""
    validator = OIDCIntrospectTokenValidator()
    token = {"active": True, "aud": "some-other-client", "scope": "openid"}

    with client_app.app.app_context(), pytest.raises(InvalidTokenError):
        validator.validate_token(token, ["openid"], request=None)


def test_api_meetings_missing_scope_in_token(
    client_app, iam_server, iam_client, iam_user, user
):
    """Test that API returns 403 when required scope is missing in token."""
    iam_token = iam_server.random_token(
        client=iam_client,
        subject=iam_user,
        scope=["profile"],
    )

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=403,
    )

    iam_server.backend.delete(iam_token)


def test_api_existing_shadow_meeting(
    client_app,
    user,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    meeting,
    iam_token,
):
    """Test that API returns existing shadow meeting for user."""
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert len(res.json["shadow-meeting"]) == 1
    assert res.json["shadow-meeting"][0] == {
        "PIN": "555555551",
        "SIPMediaGW_url": "511111111@sip.test",
        "attendee_url": shadow_meeting.attendee_url,
        "moderator_url": shadow_meeting.moderator_url,
        "name": "shadow meeting",
        "phone_number": "+33bbbphonenumber",
        "visio_code": "511111111",
    }


def test_api_existing_shadow_meeting_without_pin(
    client_app,
    user,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    meeting,
    iam_token,
):
    """Existing shadow meeting response excludes PIN and phone_number when PIN management is disabled."""
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = False
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert len(res.json["shadow-meeting"]) == 1
    assert res.json["shadow-meeting"][0] == {
        "SIPMediaGW_url": "511111111@sip.test",
        "attendee_url": shadow_meeting.attendee_url,
        "moderator_url": shadow_meeting.moderator_url,
        "name": "shadow meeting",
        "visio_code": "511111111",
    }


def test_api_existing_shadow_meeting_without_sip(
    client_app,
    user,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    meeting,
    iam_token,
):
    """Existing shadow meeting response excludes SIPMediaGW_url when SIP is disabled."""
    client_app.app.config["ENABLE_SIP"] = False
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert len(res.json["shadow-meeting"]) == 1
    assert res.json["shadow-meeting"][0] == {
        "PIN": "555555551",
        "attendee_url": shadow_meeting.attendee_url,
        "moderator_url": shadow_meeting.moderator_url,
        "name": "shadow meeting",
        "phone_number": "+33bbbphonenumber",
        "visio_code": "511111111",
    }


def test_api_existing_shadow_meeting_without_pin_and_sip(
    client_app,
    user,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    meeting,
    iam_token,
):
    """Existing shadow meeting response excludes SIP and PIN fields when both are disabled."""
    client_app.app.config["ENABLE_SIP"] = False
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = False
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert len(res.json["shadow-meeting"]) == 1
    assert res.json["shadow-meeting"][0] == {
        "attendee_url": shadow_meeting.attendee_url,
        "moderator_url": shadow_meeting.moderator_url,
        "name": "shadow meeting",
        "visio_code": "511111111",
    }


def test_api_new_shadow_meeting(
    client_app,
    user,
    meeting,
    iam_token,
):
    """Test that API creates and returns new shadow meeting if none exists."""
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert res.json["shadow-meeting"]
    assert res.json["shadow-meeting"][0]["name"] == "le séminaire de Alice Cooper"
    new_shadow_meeting = db.session.scalars(
        db.select(Meeting).where(Meeting.is_shadow.is_(True))
    ).one()
    assert (
        f"/meeting/signin/moderateur/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/invite/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["attendee_url"]
    )
    assert res.json["shadow-meeting"][0]["visio_code"]
    assert len(res.json["shadow-meeting"][0]["visio_code"]) == 9
    assert len(res.json["shadow-meeting"]) == 1
    assert len(res.json["shadow-meeting"][0]["PIN"]) == 9
    assert res.json["shadow-meeting"][0]["phone_number"]
    assert "@sip.test" in res.json["shadow-meeting"][0]["SIPMediaGW_url"]


def test_api_new_shadow_meeting_without_pin(
    client_app,
    user,
    meeting,
    iam_token,
):
    """Test that API creates and returns new shadow meeting if none exists."""
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = False
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert res.json["shadow-meeting"]
    assert res.json["shadow-meeting"][0]["name"] == "le séminaire de Alice Cooper"
    new_shadow_meeting = db.session.scalars(
        db.select(Meeting).where(Meeting.is_shadow.is_(True))
    ).one()
    assert (
        f"/meeting/signin/moderateur/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/invite/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["attendee_url"]
    )
    assert res.json["shadow-meeting"][0]["visio_code"]
    assert len(res.json["shadow-meeting"][0]["visio_code"]) == 9
    assert len(res.json["shadow-meeting"]) == 1
    assert "pin" not in res.json["shadow-meeting"][0]
    assert "phone_number" not in res.json["shadow-meeting"][0]
    assert "@sip.test" in res.json["shadow-meeting"][0]["SIPMediaGW_url"]


def test_api_new_shadow_meeting_without_sip(
    client_app,
    user,
    meeting,
    iam_token,
):
    client_app.app.config["ENABLE_SIP"] = False
    """Test that API creates and returns new shadow meeting if none exists."""
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert res.json["shadow-meeting"]
    assert res.json["shadow-meeting"][0]["name"] == "le séminaire de Alice Cooper"
    new_shadow_meeting = db.session.scalars(
        db.select(Meeting).where(Meeting.is_shadow.is_(True))
    ).one()
    assert (
        f"/meeting/signin/moderateur/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/invite/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["attendee_url"]
    )
    assert res.json["shadow-meeting"][0]["visio_code"]
    assert len(res.json["shadow-meeting"][0]["visio_code"]) == 9
    assert len(res.json["shadow-meeting"]) == 1
    assert len(res.json["shadow-meeting"][0]["PIN"]) == 9
    assert res.json["shadow-meeting"][0]["phone_number"]
    assert "SIPMediaGW_url" not in res.json["shadow-meeting"][0]


def test_api_new_shadow_meeting_without_pin_and_sip(
    client_app,
    user,
    meeting,
    iam_token,
):
    client_app.app.config["ENABLE_SIP"] = False
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = False
    """Test that API creates and returns new shadow meeting if none exists."""
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert res.json["shadow-meeting"]
    assert res.json["shadow-meeting"][0]["name"] == "le séminaire de Alice Cooper"
    new_shadow_meeting = db.session.scalars(
        db.select(Meeting).where(Meeting.is_shadow.is_(True))
    ).one()
    assert (
        f"/meeting/signin/moderateur/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/invite/{new_shadow_meeting.id}/hash/"
        in res.json["shadow-meeting"][0]["attendee_url"]
    )
    assert res.json["shadow-meeting"][0]["visio_code"]
    assert len(res.json["shadow-meeting"][0]["visio_code"]) == 9
    assert len(res.json["shadow-meeting"]) == 1
    assert "pin" not in res.json["shadow-meeting"][0]
    assert "phone_number" not in res.json["shadow-meeting"][0]
    assert "SIPMediaGW_url" not in res.json["shadow-meeting"][0]
