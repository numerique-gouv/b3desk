import time

from flask import url_for
from urllib.parse import urlparse
from urllib.parse import parse_qs


def test_signin_meeting(client_app, app, meeting, user):
    meeting_hash = meeting.get_hash("attendee")

    url = f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action


def test_signin_meeting_with_authenticated_attendee(client_app, app, meeting):
    meeting_hash = meeting.get_hash("authenticated")

    url = f"/meeting/signin/{meeting.id}/creator/{meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=302
    )

    assert response.location == "/meeting/join/1/authenticated"


def test_join_meeting_as_authenticated_attendee(
    client_app, app, meeting, authenticated_attendee
):
    url = f"/meeting/join/{meeting.id}/authenticated"
    response = client_app.get(url, status=302)

    assert "/meeting/wait/1/creator/1/hash/" in response.location
    assert "Bob%20Dylan" in response.location


def test_join_meeting_as_authenticated_attendee_with_fullname_suffix(
    client_app, app, meeting, authenticated_attendee, bbb_response
):
    meeting_hash = meeting.get_hash("authenticated")

    response = client_app.post(
        "/meeting/join",
        {
            "fullname": "Bob Dylan",
            "meeting_fake_id": meeting.id,
            "user_id": meeting.user.id,
            "h": meeting_hash,
            "fullname_suffix": "Service",
        },
        status=302,
    )

    assert (
        f"{app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName=Bob+Dylan+-+Service&"
        in response.location
    )
    assert "guest" not in response.location


def test_join_meeting_as_authenticated_attendee_with_modified_fullname(
    client_app, app, meeting, authenticated_attendee, bbb_response
):
    meeting_hash = meeting.get_hash("authenticated")

    response = client_app.post(
        "/meeting/join",
        {
            "fullname": "toto",
            "meeting_fake_id": meeting.id,
            "user_id": meeting.user.id,
            "h": meeting_hash,
            "fullname_suffix": "",
        },
    )

    assert (
        f"{app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName=Bob+Dylan&"
        in response.location
    )
    assert "guest" not in response.location


def test_join_meeting(client_app, app, meeting, bbb_response):
    meeting_hash = meeting.get_hash("attendee")
    fullname = "Bob"

    response = client_app.post(
        "/meeting/join",
        {
            "fullname": fullname,
            "meeting_fake_id": meeting.id,
            "user_id": meeting.user.id,
            "h": meeting_hash,
        },
        status=302,
    )

    assert (
        f"{app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName={fullname}"
        in response.location
    )
    assert "guest" in response.location


def test_join_mail_meeting(client_app, app, meeting, bbb_response):
    expiration = int(time.time()) + 1000
    meeting_hash = meeting.get_mail_signin_hash(meeting.id, expiration)
    fullname = "Bob"

    response = client_app.post(
        "/meeting/joinmail",
        {
            "fullname": fullname,
            "meeting_fake_id": meeting.id,
            "user_id": meeting.user.id,
            "h": meeting_hash,
            "expiration": expiration,
        },
        status=302,
    )

    assert (
        f"{app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName={fullname}"
        in response.location
    )


def test_join_meeting_as_role(
    client_app, app, authenticated_user, meeting, bbb_response
):
    fullname = "Alice+Cooper"

    response = client_app.get(f"/meeting/join/{meeting.id}/attendee", status=302)

    assert (
        f"{app.config['BIGBLUEBUTTON_ENDPOINT']}/join?fullName={fullname}"
        in response.location
    )


def test_join_meeting_as_role__meeting_not_found(
    client_app, app, authenticated_user, bbb_response
):
    client_app.get(f"/meeting/join/321/attendee", status=404)


def test_join_meeting_as_role__not_attendee_or_moderator(
    client_app, app, authenticated_user, meeting, bbb_response
):

    client_app.get(f"/meeting/join/{meeting.id}/journalist", status=404)


def test_waiting_meeting_with_a_fullname_containing_a_slash(client_app, app, meeting):
    fullname_suffix = "Service EN"
    meeting_fake_id = meeting.fake_id
    h = meeting.get_hash("attendee")
    fullname = "Alice/Cooper"

    with app.test_request_context():
        waiting_meeting_url = url_for(
            "routes.waiting_meeting",
            meeting_fake_id=meeting_fake_id,
            user_id=meeting.user.id,
            h=h,
            fullname=fullname,
            fullname_suffix=fullname_suffix,
        )
    response = client_app.get(waiting_meeting_url, status=200)

    response.mustcontain(fullname)


def test_waiting_meeting_with_empty_fullname_suffix(client_app, app, meeting):
    meeting_fake_id = meeting.fake_id
    h = meeting.get_hash("attendee")
    fullname = "Alice/Cooper"

    with app.test_request_context():
        waiting_meeting_url = url_for(
            "routes.waiting_meeting",
            meeting_fake_id=meeting_fake_id,
            user_id=meeting.user.id,
            h=h,
            fullname=fullname,
            fullname_suffix="",
        )
    client_app.get(waiting_meeting_url, status=200)
