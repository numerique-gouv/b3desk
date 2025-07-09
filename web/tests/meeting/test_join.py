import time
from urllib.parse import parse_qs
from urllib.parse import urlparse

from b3desk.models.roles import Role
from flask import url_for
from joserfc import jwt
from joserfc.jwk import RSAKey


def test_signin_meeting(client_app, meeting, user, bbb_response):
    meeting_hash = meeting.get_hash(Role.attendee)

    url = f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action

    response = response.form.submit()
    url = urlparse(response.location)
    url_role = parse_qs(url.query)["role"]
    assert url_role == ["viewer"]


def test_attendee_link_moderator_promotion_for_meeting_owner_already_authenticated(
    client_app,
    app,
    meeting,
    authenticated_user,
    bbb_response,
):
    """If the meeting owner are authenticated, they must be automatically promoted moderator in the meeting when clicking on an attendee link."""
    meeting_hash = meeting.get_hash(Role.attendee)
    url = f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"

    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )
    response = response.form.submit()
    url = urlparse(response.location)
    url_role = parse_qs(url.query)["role"]
    assert url_role == ["moderator"]


def test_signin_meeting_with_authenticated_attendee(client_app, meeting):
    meeting_hash = meeting.get_hash(Role.authenticated)

    url = f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=302
    )

    assert response.location == "/meeting/join/1/authenticated"


def test_auth_attendee_disabled(client_app, meeting):
    """If attendee authentication service is temporarily disabled, we should skip the attendee authentication step.

    https://github.com/numerique-gouv/b3desk/issues/9
    """
    client_app.app.config["OIDC_ATTENDEE_ENABLED"] = False
    meeting_hash = meeting.get_hash(Role.authenticated)

    url = f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )
    response.mustcontain("/meeting/join")


def test_join_meeting_as_authenticated_attendee(
    client_app, meeting, authenticated_attendee
):
    url = f"/meeting/join/{meeting.id}/authenticated"
    response = client_app.get(url, status=302)

    assert "/meeting/wait/1/creator/1/hash/" in response.location
    assert "Bob%20Dylan" in response.location

    response = response.follow()

    assert response.form["fullname"].value == "Bob Dylan"


def test_fix_authenticated_attendee_name_case(client_app, meeting, user):
    """The user names coming from the identity provider might be uppercase. In such cases b3desk should correct the display.

    https://github.com/numerique-gouv/b3desk/issues/47
    """
    user.given_name = "JOHN"
    user.family_name = "LENNON"
    user.email = "john@lennon.com"
    with client_app.session_transaction() as session:
        session["current_provider"] = "attendee"
        session["last_authenticated"] = "true"
        session["userinfo"] = {
            "given_name": user.given_name,
            "family_name": user.family_name,
            "email": user.email,
        }

    url = f"/meeting/join/{meeting.id}/authenticated"
    response = client_app.get(url, status=302)

    assert "/meeting/wait/1/creator/1/hash/" in response.location
    assert "John%20Lennon" in response.location

    response = response.follow()

    assert response.form["fullname"].value == "John Lennon"


def test_join_meeting_as_authenticated_attendee_with_fullname_suffix(
    client_app, meeting, authenticated_attendee, bbb_response
):
    response = client_app.get(f"/meeting/join/{meeting.id}/authenticated").follow()
    response.form["fullname_suffix"] = "Service"
    response = response.form.submit(status=302)

    assert (
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName=Bob+Dylan+-+Service&"
        in response.location
    )
    assert "guest" not in response.location


def test_join_meeting_as_authenticated_attendee_with_modified_fullname(
    client_app, meeting, authenticated_attendee, bbb_response
):
    response = client_app.get(f"/meeting/join/{meeting.id}/authenticated").follow()
    response.form["fullname"] = "toto"
    response = response.form.submit()

    assert (
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName=Bob+Dylan&"
        in response.location
    )
    assert "guest" not in response.location


def test_join_meeting(client_app, meeting, bbb_response):
    meeting_hash = meeting.get_hash(Role.attendee)
    response = client_app.get(
        f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"
    )
    response.form["fullname"] = "Bob"
    response = response.form.submit()

    assert (
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName=Bob"
        in response.location
    )
    assert "guest" in response.location


def test_join_mail_meeting(client_app, meeting, bbb_response):
    expiration = int(time.time()) + 1000
    meeting_hash = meeting.get_mail_signin_hash(meeting.id, expiration)
    response = client_app.get(
        f"/meeting/signinmail/{meeting.id}/expiration/{expiration}/hash/{meeting_hash}"
    )
    response.form["fullname"] = "Bob"
    response.form["user_id"] = meeting.user.id
    response = response.form.submit()

    assert (
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName=Bob"
        in response.location
    )


def test_join_meeting_as_role(client_app, authenticated_user, meeting, bbb_response):
    fullname = "Alice+Cooper"

    response = client_app.get(f"/meeting/join/{meeting.id}/invite", status=302)

    assert (
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName={fullname}"
        in response.location
    )


def test_join_meeting_as_role__meeting_not_found(
    client_app, authenticated_user, bbb_response
):
    client_app.get("/meeting/join/321/attendee", status=404)


def test_join_meeting_as_role__not_attendee_or_moderator(
    client_app, authenticated_user, meeting, bbb_response
):
    client_app.get(f"/meeting/join/{meeting.id}/journalist", status=404)


def test_waiting_meeting_with_a_fullname_containing_a_slash(client_app, meeting):
    fullname_suffix = "Service EN"
    meeting_fake_id = meeting.fake_id
    h = meeting.get_hash(Role.attendee)
    fullname = "Alice/Cooper"

    waiting_meeting_url = url_for(
        "join.waiting_meeting",
        meeting_fake_id=meeting_fake_id,
        creator=meeting.user,
        h=h,
        fullname=fullname,
        fullname_suffix=fullname_suffix,
    )
    response = client_app.get(waiting_meeting_url, status=200)

    response.mustcontain(fullname)


def test_waiting_meeting_with_empty_fullname_suffix(client_app, meeting):
    meeting_fake_id = meeting.fake_id
    h = meeting.get_hash(Role.attendee)
    fullname = "Alice/Cooper"

    waiting_meeting_url = url_for(
        "join.waiting_meeting",
        meeting_fake_id=meeting_fake_id,
        creator=meeting.user,
        h=h,
        fullname=fullname,
        fullname_suffix="",
    )
    client_app.get(waiting_meeting_url, status=200)


def test_join_meeting_with_sip_connect(client_app, meeting):
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": f"{client_app.app.config['PREFERRED_URL_SCHEME']}://{client_app.app.config['SERVER_NAME']}"
    }
    private_key_from_settings = RSAKey.import_key(client_app.app.config["PRIVATE_KEY"])
    token = jwt.encode(header, claims, private_key_from_settings)
    response = client_app.get(
        "/sip-connect/911111111", headers={"Authorization": token}, status=200
    )
    response.mustcontain("Rejoindre le séminaire")


def test_join_meeting_with_sip_connect_no_token(client_app, meeting):
    client_app.get("/sip-connect/911111111", status=401)


def test_join_meeting_with_sip_connect_wrong_visio_code(client_app):
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": f"{client_app.app.config['PREFERRED_URL_SCHEME']}://{client_app.app.config['SERVER_NAME']}"
    }
    private_key_from_settings = RSAKey.import_key(client_app.app.config["PRIVATE_KEY"])
    token = jwt.encode(header, claims, private_key_from_settings)
    client_app.get("/sip-connect/1", headers={"Authorization": token}, status=404)


def test_join_meeting_with_sip_connect_wrong_token(client_app):
    private_key = RSAKey.generate_key(2048, parameters={"alg": "RS256", "use": "sig"})
    private_pem_bytes = private_key.as_pem(private=True)
    private_key_from_settings = RSAKey.import_key(private_pem_bytes)
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": f"{client_app.app.config['PREFERRED_URL_SCHEME']}://{client_app.app.config['SERVER_NAME']}"
    }
    token = jwt.encode(header, claims, private_key_from_settings)

    client_app.get(
        "/sip-connect/911111111", headers={"Authorization": token}, status=401
    )


def test_join_meeting_with_sip_connect_token_with_wrong_iss_value(client_app):
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {"iss": "http://wrong-domain.org"}
    private_key_from_settings = RSAKey.import_key(client_app.app.config["PRIVATE_KEY"])
    token = jwt.encode(header, claims, private_key_from_settings)

    client_app.get(
        "/sip-connect/911111111", headers={"Authorization": token}, status=401
    )


def test_join_meeting_with_visio_code(client_app, meeting, visio_code_session):
    response = client_app.get("/home")
    response.forms[0]["visio_code1"] = "911"
    response.forms[0]["visio_code2"] = "111"
    response.forms[0]["visio_code3"] = "111"
    response = response.forms[0].submit()
    response.mustcontain("Rejoindre le séminaire")


def test_join_meeting_with_wrong_visio_code(client_app, meeting, visio_code_session):
    response = client_app.get("/home", status=200)
    response.forms[0]["visio_code1"] = "123"
    response.forms[0]["visio_code2"] = "456"
    response.forms[0]["visio_code3"] = "789"
    response = response.forms[0].submit()
    assert ("error", "Le code de connexion saisi est erroné") in response.flashes


def test_join_meeting_with_visio_code_with_authenticated_user(
    client_app, meeting, authenticated_user, user, bbb_response, visio_code_session
):
    response = client_app.get("/welcome", status=200)
    response.forms[0]["visio_code1"] = "911"
    response.forms[0]["visio_code2"] = "111"
    response.forms[0]["visio_code3"] = "111"
    response = response.forms[0].submit()
    response.mustcontain("Rejoindre le séminaire")


def test_join_meeting_with_wrong_visio_code_with_authenticated_user(
    client_app, meeting, authenticated_user, user, bbb_response, visio_code_session
):
    response = client_app.get("/welcome", status=200)
    response.forms[0]["visio_code1"] = "123"
    response.forms[0]["visio_code2"] = "456"
    response.forms[0]["visio_code3"] = "789"
    response = response.forms[0].submit()
    assert ("error", "Le code de connexion saisi est erroné") in response.flashes
