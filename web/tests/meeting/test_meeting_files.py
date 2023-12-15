from flask import url_for
from webdav3.exceptions import WebDavException


def test_nextcloud_enabled(client_app, authenticated_user, meeting):
    res = client_app.get(
        url_for("routes.edit_meeting_files", meeting_id=meeting.id), status=200
    )
    res.mustcontain("depuis le Nuage")


def test_nextcloud_authentication_issue(
    client_app, authenticated_user, meeting, mocker
):
    response = {
        "nctoken": None,
        "nclocator": None,
        "nclogin": None,
    }
    mocker.patch(
        "b3desk.models.users.make_nextcloud_credentials_request", return_value=response
    )
    res = client_app.get(
        url_for("routes.edit_meeting_files", meeting_id=meeting.id), status=200
    )
    res.mustcontain(no="depuis le Nuage")


def test_nextcloud_webdav_issue(client_app, authenticated_user, meeting, mocker):
    mocker.patch("webdav3.client.Client.list", side_effect=WebDavException)
    res = client_app.get(
        url_for("routes.edit_meeting_files", meeting_id=meeting.id),
        status=200,
        expect_errors=True,
    )
    res.mustcontain(no="depuis le Nuage")


def test_file_sharing_disabled(client_app, authenticated_user, meeting):
    client_app.app.config["FILE_SHARING"] = False
    res = client_app.get(
        url_for("routes.edit_meeting_files", meeting_id=meeting.id), status=302
    )
    assert ("warning", "Vous ne pouvez pas modifier cet élément") in res.flashes
