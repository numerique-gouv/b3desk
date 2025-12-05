import json
import os
from datetime import date

import pytest
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import get_meeting_file_hash
from flask import url_for
from webdav3.exceptions import WebDavException


def test_nextcloud_enabled(client_app, authenticated_user, meeting):
    """Test that Nextcloud file sharing UI is displayed when enabled."""
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting), status=200
    )
    res.mustcontain("depuis le Nuage")


def test_nextcloud_authentication_issue(
    client_app, authenticated_user, meeting, mocker
):
    """Test that Nextcloud UI is hidden when authentication fails."""
    response = {
        "nctoken": None,
        "nclocator": None,
        "nclogin": None,
    }
    mocker.patch(
        "b3desk.nextcloud.make_nextcloud_credentials_request", return_value=response
    )
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting), status=200
    )
    res.mustcontain(no="depuis le Nuage")


def test_nextcloud_webdav_issue(client_app, authenticated_user, meeting, mocker):
    """If the webdav healthcheck is bad, sharing buttons should not be displayed."""
    mocker.patch("webdav3.client.Client.list", side_effect=WebDavException)
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting),
        status=200,
        expect_errors=True,
    )
    res.mustcontain(no="depuis le Nuage")


def test_nextcloud_expired_token(client_app, authenticated_user, meeting, mocker):
    """Test that expired WebDAV token is renewed before failing."""
    already_attempted = False

    def webdav_list():
        nonlocal already_attempted
        if not already_attempted:
            already_attempted = True
            raise WebDavException()

    mocker.patch("webdav3.client.Client.list", side_effect=webdav_list)
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting),
        status=200,
        expect_errors=True,
    )
    assert already_attempted
    res.mustcontain("depuis le Nuage")


def test_file_sharing_disabled(client_app, authenticated_user, meeting):
    """Test that file sharing endpoint redirects when feature is disabled."""
    client_app.app.config["FILE_SHARING"] = False
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting), status=302
    )
    assert ("warning", "Vous ne pouvez pas modifier cet élément") in res.flashes


def test_add_dropzone_file(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path
):
    """Test uploading a file via dropzone chunked upload."""
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


@pytest.fixture()
def mock_meeting_is_running(mocker):
    mocker.patch("b3desk.models.meetings.Meeting.is_running", return_value=True)


def test_file_picker_called_by_bbb(
    client_app, authenticated_user, meeting, mock_meeting_is_running
):
    response = client_app.get("/meeting/1/file-picker")
    assert "meeting/file_picker.html" in vars(response)["contexts"]


def test_file_picker_callback(client_app, authenticated_user, meeting, mocker):
    post_data = ["/folder/file1.pdf", "file2.jpg"]

    mocker.patch("b3desk.tasks.background_upload.delay", return_value=True)
    client_app.post(
        f"/meeting/files/{meeting.id}/file-picker-callback",
        params=json.dumps(post_data),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        status=200,
    )


def test_ncdownload(client_app, authenticated_user, meeting, mocker, caplog):
    class FakeClient:
        def info(self, ncpath):
            return {"content_type": "application/pdf"}

        def download_sync(self, remote_path, local_path):
            pass

    meeting.user.nc_locator = "alice"
    meeting.user.nc_token = "nctoken"
    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())
    mocked_send = mocker.patch(
        "b3desk.endpoints.meeting_files.send_from_directory",
        return_value="fake_response",
    )

    response = client_app.get(
        "/ncdownload/1/7dfacbaf-8b48-4ec6-8712-951b206b0fd4/666acf548b967aaa49c24efe1d9da24ce0d22d98/1//folder/file1.pdf"
    ).follow()

    assert "Service requesting file url folder/file1.pdf" in caplog.text
    args, kwargs = mocked_send.call_args
    assert kwargs["download_name"] == "file1.pdf"
    assert kwargs["mimetype"] == "application/pdf"
    assert response.body == b"fake_response"
    args[0].startswith("/tmp/")
    args[0].endswith("/test_ncdownload0")


def test_ncdownload_with_file_not_in_db_abort_404(
    client_app, authenticated_user, caplog
):
    client_app.get("/ncdownload/0/999999/mftoken/1/badfile1.pdf", status=404)


def test_ncdownload_with_bad_token_abort_404(client_app, authenticated_user, caplog):
    client_app.get(
        "/ncdownload/1/7dfacbaf-8b48-4ec6-8712-951b206b0fd4/invalid-token/1/folder/file1.pdf",
        status=404,
    )


def test_ncdownload_webdav_exception_disables_nextcloud(
    client_app, authenticated_user, meeting, mocker
):
    """Test that WebDAV exception disables Nextcloud for non-external MeetingFiles."""
    meeting_file = MeetingFiles(
        nc_path="/folder/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
    )
    meeting_file.save()

    meeting.user.nc_locator = "alice"
    meeting.user.nc_token = "nctoken"
    meeting.user.save()

    mocker.patch(
        "b3desk.nextcloud.webdavClient",
        side_effect=WebDavException,
    )

    disable_mock = mocker.patch.object(meeting.user, "disable_nextcloud")

    token = get_meeting_file_hash(meeting_file.id, 0)
    response = client_app.get(
        f"/ncdownload/0/{meeting_file.id}/{token}/{meeting.id}/folder/test.pdf",
        status=200,
    )

    disable_mock.assert_called_once()
    assert response.json["status"] == 500
