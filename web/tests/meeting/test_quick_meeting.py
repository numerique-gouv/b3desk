from urllib.parse import parse_qs
from urllib.parse import urlparse

import pyquery
from b3desk.join import get_mail_signin_url
from b3desk.join import get_signin_url
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import get_quick_meeting_from_fake_id
from b3desk.models.roles import Role


def test_no_unauthenticated_quick_meeting(client_app, bbb_response):
    """No anonymous quick mail form should be displayed on the home page if it is not allowed by the configuration."""
    client_app.app.config["MAIL_MEETING"] = False
    res = client_app.get("/home")
    assert 1 not in res.forms.keys()


def test_unauthenticated_quick_meeting_unauthorized_email(
    client_app,
    bbb_response,
):
    """Test that unauthorized email domain cannot launch anonymous quick meeting."""
    client_app.app.config["ENABLE_LASUITENUMERIQUE"] = False
    client_app.app.config["MAIL_MEETING"] = True
    res = client_app.get("/home")
    res.forms[1]["mail"] = "email@example.test"
    res = res.forms[1].submit()
    assert (
        "error_login",
        "Ce courriel ne correspond pas à un service de l'État. Si vous appartenez à un service de l'État mais votre courriel n'est pas reconnu par Webinaire, contactez-nous pour que nous le rajoutions !",
    ) in res.flashes


def test_unauthenticated_quick_meeting_authorized_email(
    client_app,
    bbb_response,
    smtpd,
):
    """Test that authorized email domain receives meeting link via email."""
    assert len(smtpd.messages) == 0
    client_app.app.config["ENABLE_LASUITENUMERIQUE"] = False
    client_app.app.config["MAIL_MEETING"] = True
    res = client_app.get("/home")
    res.forms[1]["mail"] = "example@gouv.fr"
    res = res.forms[1].submit()
    assert (
        "success_login",
        "Vous avez reçu un courriel pour vous connecter",
    ) in res.flashes
    assert len(smtpd.messages) == 1

    message = smtpd.messages[0].get_payload()[0].get_payload(decode=True).decode()
    pq = pyquery.PyQuery(message)
    link = pq("a")[0].attrib["href"]
    assert "/meeting/signinmail/" in link

    res = client_app.get(link)
    assert res.template == "meeting/signinmail.html"


CREATE_RESPONSE = """
<response>
  <returncode>SUCCESS</returncode>
  <meetingID>Test</meetingID>
  <voiceBridge>70757</voiceBridge>
  <running>false</running>
  <attendeePW>att123</attendeePW>
  <moderatorPW>mode123</moderatorPW>
</response>
"""


def test_join_mail_meeting_with_logged_user(client_app, user, mocker):
    """Test that logged user can join meeting via email link."""

    class ResponseBBBcreate:
        content = CREATE_RESPONSE
        text = ""

    mocker.patch("requests.Session.send", return_value=ResponseBBBcreate)

    meeting = get_quick_meeting_from_fake_id()
    moderator_mail_signin_url = get_mail_signin_url(meeting)

    response = client_app.get(moderator_mail_signin_url, status=200)
    response.mustcontain("Rejoindre le séminaire")

    response.form["fullname"] = "Bob Dylan"
    response = response.form.submit()
    assert response.location.startswith("https://bbb.test/join")


def test_quick_meeting_with_logged_user(client_app, authenticated_user, mocker):
    """Test that authenticated user can create quick meeting."""

    class ResponseBBBcreate:
        content = CREATE_RESPONSE
        text = ""

    mocker.patch("requests.Session.send", return_value=ResponseBBBcreate)
    response = client_app.get("/meeting/quick", status=302)
    assert response.location.startswith("https://bbb.test/join")
    assert Meeting.query.all() == []


def test_quick_meeting_rasing_time_before_refresh_in_waiting_meeting(
    client_app, meeting, authenticated_user, mocker
):
    """Tests seconds_before_refresh increases each time waiting_meeting is refreshed and quick_meeting stays True."""

    class Response:
        content = """<response><returncode>FAIL</returncode></response>"""
        status_code = 401
        text = ""

    mocker.patch("requests.Session.send", return_value=Response)

    response = client_app.get("/meeting/quick")
    response = client_app.get(response.location)
    assert response.form["seconds_before_refresh"].value == "10"
    assert response.form["quick_meeting"].value
    response = response.form.submit()
    url = urlparse(response.location)
    url_role = parse_qs(url.query)["seconds_before_refresh"]
    assert url_role == ["15.0"]
    url_role = parse_qs(url.query)["quick_meeting"]
    assert url_role


def test_quick_meeting_signin_links_are_accessible(client_app, user):
    """Test that moderator and attendee signin links generated for quick meetings are accessible."""
    meeting = get_quick_meeting_from_fake_id()

    moderator_url = get_signin_url(meeting, Role.moderator)
    attendee_url = get_signin_url(meeting, Role.attendee)

    response = client_app.get(moderator_url, status=200)
    assert response.template == "meeting/join.html"
    assert not any(cat == "error" for cat, _ in response.flashes)

    response = client_app.get(attendee_url, status=200)
    assert response.template == "meeting/join.html"
    assert not any(cat == "error" for cat, _ in response.flashes)
