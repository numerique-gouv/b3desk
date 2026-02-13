import json
import os
from datetime import date
from datetime import datetime
from datetime import timezone

import pytest
import requests
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import assign_unique_codes
from b3desk.models.meetings import get_meeting_file_hash
from b3desk.models.users import User
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
        "b3desk.endpoints.meeting_files.is_nextcloud_available", return_value=False
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
            with open(local_path, "wb") as f:
                f.write(b"fake pdf content")

    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    nc_path = "folder/file1.pdf"
    token = get_meeting_file_hash(meeting.owner.id, nc_path)
    response = client_app.get(f"/ncdownload/{token}/{meeting.owner.id}/{nc_path}")

    assert "Service requesting file url folder/file1.pdf" in caplog.text
    assert response.status_int == 200
    assert response.content_type == "application/pdf"


def test_ncdownload_with_bad_token_abort_404(
    client_app, authenticated_user, meeting, caplog
):
    nc_path = "folder/file1.pdf"
    client_app.get(
        f"/ncdownload/invalid-token/{meeting.owner.id}/{nc_path}",
        status=404,
    )


def test_ncdownload_webdav_exception(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Test that WebDAV exception returns a 503 error but preserves credentials."""
    meeting_file = MeetingFiles(
        nc_path="/folder/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()

    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    class FakeClient:
        def info(self, ncpath):
            raise WebDavException()

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    nc_path = "folder/test.pdf"
    token = get_meeting_file_hash(meeting.owner.id, nc_path)
    response = client_app.get(
        f"/ncdownload/{token}/{meeting.owner.id}/{nc_path}",
        expect_errors=True,
    )

    # WebDavException is handled by global error handler, returns HTTP 200 with error in JSON
    assert response.status_int == 200
    assert "indisponible" in response.json["msg"]
    db.session.refresh(meeting.owner)
    assert meeting.owner.nc_locator is not None
    assert meeting.owner.nc_token is not None


def test_download_meeting_file_from_nextcloud(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Download a file stored in Nextcloud."""
    meeting_file = MeetingFiles(
        nc_path="/visio-agents/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)

    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    class FakeClient:
        def list(self):
            return []

        def download_sync(self, remote_path, local_path):
            with open(local_path, "wb") as f:
                f.write(b"fake content")

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    url = url_for(
        "meeting_files.download_meeting_files",
        meeting=meeting,
        meeting_file=meeting_file,
    )
    response = client_app.get(url)

    assert response.status_code == 200
    assert response.content_type == "application/pdf"


def test_download_meeting_file_without_webdav_credentials(
    client_app, authenticated_user, meeting, mocker
):
    """Download file redirects when Nextcloud connection fails."""
    meeting_file = MeetingFiles(
        nc_path="/visio-agents/test.pdf",
        title="test.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()

    mocker.patch(
        "b3desk.endpoints.meeting_files.is_nextcloud_available", return_value=False
    )

    url = url_for(
        "meeting_files.download_meeting_files",
        meeting=meeting,
        meeting_file=meeting_file,
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
        expect_errors=True,
    )

    assert response.status_int == 503
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
        expect_errors=True,
    )

    assert response.status_int == 503
    assert "indisponible" in response.json["msg"]


def test_download_file_for_bbb_without_webdav_credentials(client_app, meeting, mocker):
    """download_file returns error when Nextcloud connection fails."""
    mocker.patch(
        "b3desk.endpoints.meeting_files.is_nextcloud_available", return_value=False
    )

    nc_path = "folder/file.pdf"
    token = get_meeting_file_hash(meeting.owner.id, nc_path)
    response = client_app.get(
        f"/ncdownload/{token}/{meeting.owner.id}/{nc_path}",
        expect_errors=True,
    )

    assert response.status_int == 503
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

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_int == 200
    assert response.json["title"] == "file.jpg"


def test_add_dropzone_file_sqlalchemy_error(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path, mocker
):
    """SQLAlchemy error during dropzone upload cleans up Nextcloud file."""
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

    clean_called_with = []

    class FakeClient:
        def mkdir(self, path):
            pass

        def upload_sync(self, remote_path, local_path):
            pass

        def clean(self, path):
            clean_called_with.append(path)

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    mocker.patch(
        "b3desk.endpoints.meeting_files.db.session.commit",
        side_effect=exc.IntegrityError("statement", "params", "orig"),
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 409
    assert "déjà été mis en ligne" in response.json["msg"]
    assert clean_called_with == ["visio-agents/file.jpg"]


def test_add_dropzone_file_sqlalchemy_error_cleanup_fails(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path, mocker, caplog
):
    """SQLAlchemy error with failed Nextcloud cleanup logs warning but returns original error."""
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

        def clean(self, path):
            raise WebDavException("Nextcloud unavailable")

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    mocker.patch(
        "b3desk.endpoints.meeting_files.db.session.commit",
        side_effect=exc.IntegrityError("statement", "params", "orig"),
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 409
    assert "déjà été mis en ligne" in response.json["msg"]
    assert "Failed to cleanup Nextcloud file" in caplog.text


def test_add_nextcloud_file_upload(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Test nominal path: add file from Nextcloud."""
    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    class FakeClient:
        def info(self, path):
            return {"size": 1000}

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "nextcloud", "value": "/folder/doc.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_int == 200
    assert response.json["title"] == "doc.pdf"


def test_add_nextcloud_file_sqlalchemy_error(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """SQLAlchemy error returns appropriate error message."""
    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    class FakeClient:
        def info(self, path):
            return {"size": 1000}

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

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
        expect_errors=True,
    )

    assert response.status_int == 409
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

    assert response.status_int == 200
    assert response.json["title"] == "doc.pdf"


def test_add_url_file_sqlalchemy_error(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """SQLAlchemy error during URL file add returns appropriate error message."""
    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    meeting.owner.nc_last_auto_enroll = datetime.now()
    meeting.owner.last_connection_utc_datetime = datetime.now(timezone.utc)
    db.session.add(meeting.owner)
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
        expect_errors=True,
    )

    assert response.status_int == 409
    assert "déjà été mis en ligne" in response.json["msg"]


def test_add_nextcloud_file_too_large(
    client_app, authenticated_user, meeting, mocker, nextcloud_credentials
):
    """Test error when Nextcloud file exceeds max upload size."""
    meeting.owner.nc_login = nextcloud_credentials["nclogin"]
    meeting.owner.nc_locator = nextcloud_credentials["nclocator"]
    meeting.owner.nc_token = nextcloud_credentials["nctoken"]
    db.session.add(meeting.owner)
    db.session.commit()

    class FakeClient:
        def info(self, path):
            return {"size": 999999999}

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "nextcloud", "value": "/folder/huge.pdf"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 413
    assert "trop volumineux" in response.json["msg"]


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

    res = dropzone_post(status=409)
    assert "Le fichier a déjà été mis en ligne" in res.json["msg"]


def test_add_dropzone_file_too_large(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path, mocker
):
    """Test that uploading a file larger than MAX_SIZE_UPLOAD returns 413."""
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
            pass  # pragma: no cover

        def upload_sync(self, remote_path, local_path):
            pass  # pragma: no cover

    mocker.patch("b3desk.nextcloud.WebDAVClient", return_value=FakeClient())
    client_app.app.config["MAX_SIZE_UPLOAD"] = 10

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "upload", "value": "file.jpg"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 413
    assert "trop volumineux" in response.json["msg"]


def test_upload_file_chunks_disk_write_error(
    client_app, authenticated_user, meeting, jpg_file_content, mocker
):
    """Test that OSError during disk write returns 500."""
    mocker.patch(
        "b3desk.endpoints.meeting_files.open", side_effect=OSError("Disk full")
    )

    response = client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": len(jpg_file_content),
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
        expect_errors=True,
    )

    assert response.status_int == 500
    assert "Erreur lors de l'écriture" in response.json["msg"]


def test_upload_file_chunks_forbidden_mime_type(
    client_app, authenticated_user, meeting, tmp_path
):
    """Test that uploading a file with forbidden MIME type returns 400."""
    # Create a minimal valid ZIP file (forbidden MIME type)
    zip_content = (
        b"PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00test.txtPK"
        b"\x01\x02\x14\x00\x14\x00\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00test.txtPK\x05\x06\x00\x00"
        b"\x00\x00\x01\x00\x01\x006\x00\x00\x00$\x00\x00\x00\x00\x00"
    )

    response = client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": len(zip_content),
        },
        upload_files=[("dropzoneFiles", "archive.zip", zip_content)],
        expect_errors=True,
    )

    assert response.status_int == 400
    assert "Type de fichier non autorisé" in response.json["msg"]


def test_upload_file_chunks_size_mismatch(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path
):
    """Test that size mismatch between declared and actual file returns 400."""
    response = client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 1,
            "dztotalfilesize": len(jpg_file_content) + 100,  # Wrong size
        },
        upload_files=[("dropzoneFiles", "file.jpg", jpg_file_content)],
        expect_errors=True,
    )

    assert response.status_int == 400
    assert "Erreur de taille du fichier" in response.json["msg"]


def test_upload_file_chunks_not_last_chunk(
    client_app, authenticated_user, meeting, jpg_file_content, tmp_path
):
    """Test uploading intermediate chunks (not the last one)."""
    chunk1 = jpg_file_content[:50]
    chunk2 = jpg_file_content[50:]

    response = client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 0,
            "dzchunkbyteoffset": 0,
            "dztotalchunkcount": 2,
            "dztotalfilesize": len(jpg_file_content),
        },
        upload_files=[("dropzoneFiles", "file.jpg", chunk1)],
    )

    assert response.status_int == 200
    assert response.json["msg"] == "ok"

    response = client_app.post(
        f"/meeting/files/{meeting.id}/upload",
        {
            "dzchunkindex": 1,
            "dzchunkbyteoffset": 50,
            "dztotalchunkcount": 2,
            "dztotalfilesize": len(jpg_file_content),
        },
        upload_files=[("dropzoneFiles", "file.jpg", chunk2)],
    )

    assert response.status_int == 200


def test_add_meeting_files_invalid_from(client_app, authenticated_user, meeting):
    """Test add_meeting_files with invalid 'from' value returns 400."""
    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "invalid", "value": "test"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 400
    assert "no file provided" in response.json["msg"]


def test_download_meeting_file_not_found(client_app, authenticated_user, meeting):
    """Test download when file_id doesn't match any file in meeting."""
    response = client_app.get(
        f"/meeting/files/{meeting.id}/99999/download",
        expect_errors=True,
    )

    assert response.status_int == 404


def test_download_meeting_file_from_url(
    client_app, authenticated_user, meeting, mocker
):
    """Test downloading a file that has a URL (not from Nextcloud)."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()

    mock_response = mocker.Mock()
    mock_response.content = b"fake pdf content"
    mocker.patch.object(requests, "get", return_value=mock_response)

    response = client_app.get(
        url_for(
            "meeting_files.download_meeting_files",
            meeting=meeting,
            meeting_file=meeting_file,
        ),
    )

    assert response.status_int == 200


def test_add_url_file_not_available(client_app, authenticated_user, meeting, mocker):
    """Test adding a URL file when the URL is not available."""
    mock_head = mocker.Mock()
    mock_head.ok = False
    mocker.patch.object(requests, "head", return_value=mock_head)

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "URL", "value": "https://example.com/notfound.pdf"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 400
    assert "non disponible" in response.json["msg"]


def test_add_url_file_network_error(client_app, authenticated_user, meeting, mocker):
    """Test adding a URL file when a network error occurs."""
    mocker.patch.object(
        requests,
        "head",
        side_effect=requests.exceptions.Timeout("Connection timed out"),
    )

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "URL", "value": "https://example.com/timeout.pdf"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 400
    assert "non disponible" in response.json["msg"]


def test_add_url_file_too_large(client_app, authenticated_user, meeting, mocker):
    """Test adding a URL file when the file is too large."""
    mock_head = mocker.Mock()
    mock_head.ok = True
    mock_head.headers = {"content-length": "999999999"}
    mocker.patch.object(requests, "head", return_value=mock_head)

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "URL", "value": "https://example.com/huge.pdf"}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 413
    assert "trop volumineux" in response.json["msg"]


def test_add_url_file_no_content_length(
    client_app, authenticated_user, meeting, mocker
):
    """Test adding a URL file when content-length header is missing."""
    mock_head = mocker.Mock()
    mock_head.ok = True
    mock_head.headers = {}
    mocker.patch.object(requests, "head", return_value=mock_head)

    response = client_app.post(
        url_for("meeting_files.add_meeting_files", meeting=meeting),
        params=json.dumps({"from": "URL", "value": "https://example.com/nosize.pdf"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_int == 200
    assert response.json["title"] == "nosize.pdf"


def test_toggledownload_success(client_app, authenticated_user, meeting):
    """Test successful toggle of downloadable status."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
        is_downloadable=False,
    )
    db.session.add(meeting_file)
    db.session.commit()

    response = client_app.post(
        url_for(
            "meeting_files.toggledownload",
            meeting=meeting,
            meeting_file=meeting_file,
        ),
        params=json.dumps({"value": True}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_int == 200
    assert response.json["id"] == meeting_file.id
    db.session.refresh(meeting_file)
    assert meeting_file.is_downloadable is True


def test_toggledownload_not_found(client_app, authenticated_user, meeting):
    """Test toggle on non-existent file returns 404."""
    response = client_app.post(
        f"/meeting/files/{meeting.id}/99999/toggledownload",
        params=json.dumps({"value": True}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 404


def test_toggledownload_not_owner(client_app, authenticated_user, meeting):
    """Test toggle by non-owner returns 403."""
    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=other_meeting.id,
        owner=other_user,
    )
    db.session.add(meeting_file)
    db.session.commit()

    response = client_app.post(
        url_for(
            "meeting_files.toggledownload",
            meeting=other_meeting,
            meeting_file=meeting_file,
        ),
        params=json.dumps({"value": True}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 403


def test_toggledownload_file_not_in_meeting(
    client_app, authenticated_user, meeting, meeting_2
):
    """Test toggle returns 404 when file doesn't belong to meeting in URL."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting_2.id,
        owner=meeting_2.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()

    response = client_app.post(
        f"/meeting/files/{meeting.id}/{meeting_file.id}/toggledownload",
        params=json.dumps({"value": True}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 404


def test_download_file_not_in_meeting(
    client_app, authenticated_user, meeting, meeting_2
):
    """Test download returns 404 when file doesn't belong to meeting in URL."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting_2.id,
        owner=meeting_2.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()

    response = client_app.get(
        f"/meeting/files/{meeting.id}/{meeting_file.id}/download",
        expect_errors=True,
    )

    assert response.status_int == 404


def test_delete_meeting_file_success(client_app, authenticated_user, meeting):
    """Test successful deletion of a meeting file."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()
    file_id = meeting_file.id

    response = client_app.post(
        url_for("meeting_files.delete_meeting_file"),
        params=json.dumps({"id": file_id}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_int == 200
    assert response.json["id"] == file_id
    assert "supprimé avec succès" in response.json["msg"]
    assert db.session.get(MeetingFiles, file_id) is None


def test_delete_meeting_file_not_found(client_app, authenticated_user):
    """Test deletion of non-existent file returns 404."""
    response = client_app.post(
        url_for("meeting_files.delete_meeting_file"),
        params=json.dumps({"id": 99999}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 404
    assert "introuvable" in response.json["msg"]


def test_delete_meeting_file_not_owner(client_app, authenticated_user, meeting):
    """Test deletion by non-owner returns 403."""
    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=other_meeting.id,
        owner=other_user,
    )
    db.session.add(meeting_file)
    db.session.commit()
    file_id = meeting_file.id

    response = client_app.post(
        url_for("meeting_files.delete_meeting_file"),
        params=json.dumps({"id": file_id}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 403
    assert "ne pouvez pas supprimer" in response.json["msg"]
