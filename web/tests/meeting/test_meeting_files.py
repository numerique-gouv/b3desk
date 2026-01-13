import json
import os
from datetime import date
from datetime import datetime
from datetime import timezone

import pytest
import requests
from b3desk.models import db
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import get_meeting_file_hash
from b3desk.session import user_needed
from flask import url_for
from sqlalchemy import exc
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
        "/meeting/files/1/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": 134,
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
    )

    assert res.json["msg"] == "ok"

    with open(os.path.join(tmp_path, "chunks", "1-1-file.jpg"), "rb") as fd:
        assert jpg_file_content == fd.read()


@pytest.fixture()
def mock_meeting_is_running(mocker):
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=True)


def test_file_picker_called_by_bbb(
    client_app, authenticated_user, meeting, mock_meeting_is_running
):
    url = url_for("meeting_files.file_picker", bbb_meeting_id=meeting.meetingID)
    response = client_app.get(url)
    assert "meeting/file_picker.html" in vars(response)["contexts"]


def test_file_picker_callback(client_app, authenticated_user, meeting, mocker):
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


def test_file_picker_invalid_signature_returns_404(client_app, authenticated_user):
    """SignedConverter returns 404 when signature is invalid."""
    client_app.get("/meeting/invalid-signature/file-picker", status=404)


def test_user_needed_decorator_aborts_403_without_session(client_app, mocker):
    """user_needed decorator returns 403 when user session is missing."""
    mocker.patch("b3desk.session.has_user_session", return_value=False)

    @user_needed
    def protected_view(user):  # pragma: no cover
        return "ok"

    with pytest.raises(Exception) as exc_info:
        protected_view()

    assert exc_info.value.code == 403


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
        owner=meeting.user,
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


def test_download_meeting_file_from_nextcloud(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Download a file stored in Nextcloud."""
    meeting_file = MeetingFiles(
        nc_path="/visio-agents/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.user,
    )
    db.session.add(meeting_file)

    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.user)
    db.session.commit()

    class FakeClient:
        def download_sync(self, remote_path, local_path):
            with open(local_path, "wb") as f:
                f.write(b"fake content")

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    url = url_for(
        "meeting_files.download_meeting_files",
        meeting=meeting,
        file_id=meeting_file.id,
    )
    response = client_app.get(url)

    assert response.status_code == 200
    assert response.content_type == "application/pdf"


def test_download_meeting_file_without_webdav_credentials(
    client_app, authenticated_user, meeting, mocker
):
    """Download file redirects when user has no WebDAV credentials."""
    meeting_file = MeetingFiles(
        nc_path="/visio-agents/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.user,
    )
    db.session.add(meeting_file)
    db.session.commit()

    mocker.patch(
        "b3desk.endpoints.meeting_files.create_webdav_client", return_value=None
    )

    url = url_for(
        "meeting_files.download_meeting_files",
        meeting=meeting,
        file_id=meeting_file.id,
    )
    response = client_app.get(url, status=302)

    assert any(
        cat == "error" and "indisponible" in msg for cat, msg in response.flashes
    )


def test_add_dropzone_file_without_webdav_credentials(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path, mocker
):
    """Add dropzone file returns error when user has no WebDAV credentials."""
    client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": len(jpg_file_content),
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
    )

    mocker.patch(
        "b3desk.endpoints.meeting_files.create_webdav_client", return_value=None
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 500
    assert "indisponible" in response.json["msg"]


def test_add_nextcloud_file_without_webdav_credentials(
    client_app, authenticated_user, meeting, mocker
):
    """Add Nextcloud file returns error when user has no WebDAV credentials."""
    mocker.patch(
        "b3desk.endpoints.meeting_files.create_webdav_client", return_value=None
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "nextcloud", "value": "/folder/doc.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 500
    assert "indisponible" in response.json["msg"]


def test_download_file_for_bbb_without_webdav_credentials(client_app, meeting, mocker):
    """download_file returns error when user has no WebDAV credentials."""
    mocker.patch(
        "b3desk.endpoints.meeting_files.create_webdav_client", return_value=None
    )

    nc_path = "folder/file.pdf"
    token = get_meeting_file_hash(meeting.user.id, nc_path)
    response = client_app.get(
        f"/ncdownload/{token}/{meeting.user.id}/{nc_path}",
        status=200,
    )

    assert response.json["status"] == 500
    assert "indisponible" in response.json["msg"]


def test_add_dropzone_file_upload_to_nextcloud(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path, mocker
):
    """Test nominal path: upload dropzone file to Nextcloud."""
    client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": len(jpg_file_content),
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
    )

    class FakeClient:
        def mkdir(self, path):
            pass

        def upload_sync(self, remote_path, local_path):
            pass

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 200
    assert response.json["title"] == "file.jpg"


def test_add_dropzone_file_sqlalchemy_error(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path, mocker
):
    """SQLAlchemy error during dropzone upload returns appropriate error message."""
    client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": len(jpg_file_content),
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
    )

    class FakeClient:
        def mkdir(self, path):
            pass

        def upload_sync(self, remote_path, local_path):
            pass

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    mocker.patch(
        "b3desk.endpoints.meeting_files.db.session.commit",
        side_effect=exc.IntegrityError("statement", "params", "orig"),
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 500
    assert "déjà été mis en ligne" in response.json["msg"]


def test_add_nextcloud_file_upload(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Test nominal path: add file from Nextcloud."""
    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.user)
    db.session.commit()

    class FakeClient:
        def info(self, path):
            return {"size": 1000}

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "nextcloud", "value": "/folder/doc.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 200
    assert response.json["title"] == "doc.pdf"


def test_add_nextcloud_file_sqlalchemy_error(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """SQLAlchemy error returns appropriate error message."""
    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.user)
    db.session.commit()

    class FakeClient:
        def info(self, path):
            return {"size": 1000}

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    original_commit = db.session.commit
    call_count = [0]

    def commit_with_error():
        call_count[0] += 1
        if call_count[0] > 1:
            raise exc.IntegrityError("statement", "params", "orig")
        original_commit()

    mocker.patch(
        "b3desk.endpoints.meeting_files.db.session.commit",
        side_effect=commit_with_error,
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "nextcloud", "value": "/folder/doc.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 500
    assert "déjà été mis en ligne" in response.json["msg"]


def test_add_url_file(client_app, authenticated_user, meeting, mocker):
    """Test adding a file from URL."""
    mock_head = mocker.Mock()
    mock_head.ok = True
    mock_head.headers = {"content-length": "1000"}
    mocker.patch.object(requests, "head", return_value=mock_head)
    mocker.patch.object(requests, "get", return_value=mocker.Mock())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "URL", "value": "https://example.com/doc.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 200
    assert response.json["title"] == "doc.pdf"


def test_add_url_file_sqlalchemy_error(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """SQLAlchemy error during URL file add returns appropriate error message."""
    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    meeting.user.nc_last_auto_enroll = datetime.now()
    meeting.user.last_connection_utc_datetime = datetime.now(timezone.utc)
    db.session.add(meeting.user)
    db.session.commit()

    mock_head = mocker.Mock()
    mock_head.ok = True
    mock_head.headers = {"content-length": "1000"}
    mocker.patch.object(requests, "head", return_value=mock_head)
    mocker.patch.object(requests, "get", return_value=mocker.Mock())

    mocker.patch(
        "b3desk.endpoints.meeting_files.db.session.commit",
        side_effect=exc.IntegrityError("statement", "params", "orig"),
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "URL", "value": "https://example.com/doc.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 500
    assert "déjà été mis en ligne" in response.json["msg"]


def test_add_nextcloud_file_too_large(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Test error when Nextcloud file exceeds max upload size."""
    meeting.user.nc_login = nextcloud_credentials["nclogin"]
    meeting.user.nc_locator = nextcloud_credentials["nclocator"]
    meeting.user.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.user)
    db.session.commit()

    class FakeClient:
        def info(self, path):
            return {"size": 999999999}

    mocker.patch("b3desk.nextcloud.webdavClient", return_value=FakeClient())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "nextcloud", "value": "/folder/huge.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.json["status"] == 500
    assert "TROP VOLUMINEUX" in response.json["msg"]


def test_file_picker_meeting_not_running(
    client_app, authenticated_user, meeting, mocker
):
    """Test file picker redirects when meeting is not running."""
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)

    url = url_for("meeting_files.file_picker", bbb_meeting_id=meeting.meetingID)
    response = client_app.get(url, status=302)

    assert any(
        cat == "error" and "pas en cours" in msg for cat, msg in response.flashes
    )


def test_add_dropzone_file_already_added(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path
):
    """Test uploading a file via dropzone chunked upload."""

    def dropzone_post(status):
        return client_app.post(
            "/meeting/files/1/upload",
            {
                "dzchunkindex": 0,
                "dzchunkbyteoffset": 0,
                "dztotalchunkcount": 1,
                "dztotalfilesize": 134,
            },
            upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
            status=status,
        )

    res = dropzone_post(status=200)
    assert res.json["msg"] == "ok"
    with open(os.path.join(tmp_path, "chunks", "1-1-file.jpg"), "rb") as fd:
        assert jpg_file_content == fd.read()

    res = dropzone_post(status=500)
    assert "Le fichier a déjà été mis en ligne" in res.json["msg"]
