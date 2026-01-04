import json
import os
from datetime import date

import pytest
from b3desk.models import db
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
    """Test that Nextcloud buttons are disabled when authentication fails."""
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
    res.mustcontain("disabled")
    res.mustcontain(no="onClick=openNCFilePicker")


def test_nextcloud_webdav_issue(client_app, authenticated_user, meeting, mocker):
    """If Nextcloud is marked unavailable, sharing buttons should be disabled."""
    mocker.patch(
        "b3desk.endpoints.meeting_files.check_nextcloud_connection", return_value=False
    )
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting),
        status=200,
    )
    res.mustcontain("disabled")
    res.mustcontain(no="onClick=openNCFilePicker")


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
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=True)


def test_file_picker_called_by_bbb(
    client_app, authenticated_user, meeting, mock_meeting_is_running
):
    from flask import url_for

    url = url_for("meeting_files.file_picker", bbb_meeting_id=meeting.meetingID)
    response = client_app.get(url)
    assert "meeting/file_picker.html" in vars(response)["contexts"]


def test_file_picker_callback(client_app, authenticated_user, meeting, mocker):
    from flask import url_for

    post_data = ["/folder/file1.pdf", "file2.jpg"]

    mocker.patch("b3desk.tasks.background_upload.delay", return_value=True)
    url = url_for(
        "meeting_files.file_picker_callback", bbb_meeting_id=meeting.meetingID
    )
    client_app.post(
        url,
        params=json.dumps(post_data),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        status=200,
    )


def test_ncdownload(
    client_app, authenticated_user, meeting, mocker, caplog, nextcloud_credentials
):
    class FakeClient:
        def info(self, ncpath):
            return {"content_type": "application/pdf"}

        def download_sync(self, remote_path, local_path):
            pass

    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.user)
    db.session.commit()

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())
    mocked_send = mocker.patch(
        "b3desk.endpoints.meeting_files.send_from_directory",
        return_value="fake_response",
    )

    nc_path = "folder/file1.pdf"
    token = get_meeting_file_hash(meeting.user.id, nc_path)
    response = client_app.get(f"/ncdownload/{token}/{meeting.user.id}/{nc_path}")

    assert "Service requesting file url folder/file1.pdf" in caplog.text
    args, kwargs = mocked_send.call_args
    assert kwargs["download_name"] == "file1.pdf"
    assert kwargs["mimetype"] == "application/pdf"
    assert response.body == b"fake_response"
    args[0].startswith("/tmp/")
    args[0].endswith("/test_ncdownload0")


def test_ncdownload_with_bad_token_abort_404(
    client_app, authenticated_user, meeting, caplog
):
    nc_path = "folder/file1.pdf"
    client_app.get(
        f"/ncdownload/invalid-token/{meeting.user.id}/{nc_path}",
        status=404,
    )


def test_ncdownload_webdav_exception(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Test that WebDAV exception returns a 500 error but preserves credentials."""
    meeting_file = MeetingFiles(
        nc_path="/folder/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
    )
    db.session.add(meeting_file)
    db.session.commit()

    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.user)
    db.session.commit()

    class FakeClient:
        def info(self, ncpath):
            raise WebDavException()

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    nc_path = "folder/test.pdf"
    token = get_meeting_file_hash(meeting.user.id, nc_path)
    response = client_app.get(
        f"/ncdownload/{token}/{meeting.user.id}/{nc_path}",
        status=200,
    )

    assert response.json["status"] == 500
    db.session.refresh(meeting.user)
    assert meeting.user.nc_locator is not None
    assert meeting.user.nc_token is not None
