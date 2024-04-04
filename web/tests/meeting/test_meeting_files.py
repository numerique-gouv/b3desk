import os

from flask import url_for
from webdav3.exceptions import WebDavException


def test_nextcloud_enabled(client_app, authenticated_user, meeting):
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting), status=200
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
        url_for("meeting_files.edit_meeting_files", meeting=meeting), status=200
    )
    res.mustcontain(no="depuis le Nuage")


def test_nextcloud_webdav_issue(client_app, authenticated_user, meeting, mocker):
    mocker.patch("webdav3.client.Client.list", side_effect=WebDavException)
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting),
        status=200,
        expect_errors=True,
    )
    res.mustcontain(no="depuis le Nuage")


def test_file_sharing_disabled(client_app, authenticated_user, meeting):
    client_app.app.config["FILE_SHARING"] = False
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting), status=302
    )
    assert ("warning", "Vous ne pouvez pas modifier cet élément") in res.flashes


def test_add_dropzone_file(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path
):
    res = client_app.post(
        "/meeting/files/1/dropzone",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": 134,
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
    )

    assert res.text == "Chunk upload successful"

    with open(os.path.join(tmp_path, "dropzone", "1-1-file.jpg"), "rb") as fd:
        assert jpg_file_content == fd.read()
