import pytest
import requests
from b3desk.commands import bp
from b3desk.docs import create_child_document
from b3desk.docs import create_document
from b3desk.docs import document_url
from b3desk.docs import get_document
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import RecordingDocument

RECORDING_ID = "rec-ai-1"
SUMMARY_URL = "https://bbb.test/ai-summary/rec-ai-1/ai-summary.md"


@pytest.fixture
def docs_client(mocker):
    """Mock the Docs API client, as seen from the endpoint."""

    class Client:
        get_document = mocker.patch(
            "b3desk.endpoints.docs.get_document", return_value={"id": "parent-id"}
        )
        create_document = mocker.patch(
            "b3desk.endpoints.docs.create_document", return_value={"id": "parent-id"}
        )
        create_child_document = mocker.patch(
            "b3desk.endpoints.docs.create_child_document",
            return_value={"id": "child-id"},
        )

    return Client


@pytest.fixture
def summary_download(mocker):
    """Mock the download of the Markdown summary from BBB."""
    response = mocker.MagicMock()
    response.content = b"# Summary"
    return mocker.patch("b3desk.endpoints.docs.requests.get", return_value=response)


@pytest.fixture
def docs_authorization(mocker):
    """Mock the ProConnect authorization flow used to reach Docs."""
    mocker.patch(
        "authlib.integrations.flask_client.apps.FlaskOAuth2App.authorize_access_token",
        return_value={"access_token": "access-tok"},
    )


def start_export(client_app, meeting, recording_id=RECORDING_ID):
    """Register the export target in session, as the push endpoint does."""
    with client_app.session_transaction() as session:
        session["docs_push_target"] = {
            "meeting_id": meeting.id,
            "recording_id": recording_id,
        }


def test_create_document(app, mocker):
    """create_document posts the title to the Docs external API with the bearer token."""
    app.config["DOCS_API_URL"] = "https://docs.example"
    post = mocker.patch("b3desk.docs.requests.post")
    post.return_value.json.return_value = {"id": "abc"}

    with app.app_context():
        result = create_document("access-tok", "Meeting")

    assert result == {"id": "abc"}
    args, kwargs = post.call_args
    assert args[0] == "https://docs.example/external_api/v1.0/documents/"
    assert kwargs["headers"]["Authorization"] == "Bearer access-tok"
    assert kwargs["json"] == {"title": "Meeting"}
    post.return_value.raise_for_status.assert_called_once()


def test_create_child_document(app, mocker):
    """create_child_document uploads the summary below the meeting document.

    Docs titles the document after the file name, which therefore carries no
    extension.
    """
    app.config["DOCS_API_URL"] = "https://docs.example"
    post = mocker.patch("b3desk.docs.requests.post")
    post.return_value.json.return_value = {"id": "child"}

    with app.app_context():
        result = create_child_document("access-tok", "parent", "2018-07-04", b"# hi")

    assert result == {"id": "child"}
    args, kwargs = post.call_args
    assert (
        args[0] == "https://docs.example/external_api/v1.0/documents/parent/children/"
    )
    assert kwargs["headers"]["Authorization"] == "Bearer access-tok"
    assert kwargs["files"]["file"] == ("2018-07-04", b"# hi", "text/markdown")


def test_get_document(app, mocker):
    """get_document returns the document described by the Docs API."""
    app.config["DOCS_API_URL"] = "https://docs.example"
    get = mocker.patch("b3desk.docs.requests.get")
    get.return_value.status_code = 200
    get.return_value.json.return_value = {"id": "abc"}

    with app.app_context():
        result = get_document("access-tok", "abc")

    assert result == {"id": "abc"}
    assert (
        get.call_args.args[0] == "https://docs.example/external_api/v1.0/documents/abc/"
    )


@pytest.mark.parametrize("status_code", [403, 404])
def test_get_document_unreachable(app, mocker, status_code):
    """get_document returns nothing for a document the user cannot read anymore."""
    app.config["DOCS_API_URL"] = "https://docs.example"
    get = mocker.patch("b3desk.docs.requests.get")
    get.return_value.status_code = status_code

    with app.app_context():
        assert get_document("access-tok", "abc") is None


def test_document_url(app):
    """document_url points at the page where a user reads a document."""
    app.config["DOCS_API_URL"] = "https://docs.example/"

    with app.app_context():
        assert document_url("abc") == "https://docs.example/docs/abc/"


def test_docs_routes_absent_when_disabled(app):
    """The Docs blueprint is not registered when the feature is disabled."""
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "docs.push_recording_to_docs" not in endpoints


@pytest.mark.docs
def test_export_creates_meeting_document_and_session_subdocument(
    client_app,
    authenticated_user,
    meeting,
    bbb_getRecordings_ai_summary,
    docs_authorization,
    docs_client,
    summary_download,
):
    """The first export creates the meeting document and the session sub-document."""
    start_export(client_app, meeting)

    response = client_app.get("/docs_callback", status=302)

    docs_client.create_document.assert_called_once_with("access-tok", meeting.name)
    docs_client.create_child_document.assert_called_once_with(
        "access-tok", "parent-id", "Meeting with summary", b"# Summary"
    )
    assert summary_download.call_args.args[0] == SUMMARY_URL

    meeting = db.session.get(Meeting, meeting.id)
    assert meeting.docs_document_id == "parent-id"
    assert meeting.docs_document_id_for_recording(RECORDING_ID) == "child-id"
    assert f"meeting/recordings/{meeting.id}" in response.location


@pytest.mark.docs
def test_export_reuses_the_meeting_document(
    client_app,
    authenticated_user,
    meeting,
    bbb_getRecordings_ai_summary,
    docs_authorization,
    docs_client,
    summary_download,
):
    """A meeting already holding a Docs document gets no second one."""
    meeting.docs_document_id = "parent-id"
    db.session.commit()
    start_export(client_app, meeting)

    client_app.get("/docs_callback", status=302)

    docs_client.get_document.assert_called_once_with("access-tok", "parent-id")
    docs_client.create_document.assert_not_called()
    docs_client.create_child_document.assert_called_once()


@pytest.mark.docs
def test_export_recreates_a_deleted_meeting_document(
    client_app,
    authenticated_user,
    meeting,
    bbb_getRecordings_ai_summary,
    docs_authorization,
    docs_client,
    summary_download,
):
    """A meeting document deleted in Docs is created again."""
    meeting.docs_document_id = "gone"
    db.session.commit()
    docs_client.get_document.return_value = None
    docs_client.create_document.return_value = {"id": "new-parent"}
    start_export(client_app, meeting)

    client_app.get("/docs_callback", status=302)

    docs_client.create_document.assert_called_once_with("access-tok", meeting.name)
    assert db.session.get(Meeting, meeting.id).docs_document_id == "new-parent"


@pytest.mark.docs
def test_export_failure_keeps_the_meeting_document(
    client_app,
    authenticated_user,
    meeting,
    bbb_getRecordings_ai_summary,
    docs_authorization,
    docs_client,
    summary_download,
):
    """A failing upload keeps the meeting document, and records no sub-document."""
    docs_client.create_child_document.side_effect = requests.RequestException
    start_export(client_app, meeting)

    response = client_app.get("/docs_callback", status=302).follow(status=200)

    assert "L’enregistrement du compte rendu dans Docs a échoué." in response.text
    meeting = db.session.get(Meeting, meeting.id)
    assert meeting.docs_document_id == "parent-id"
    assert meeting.recording_documents == []


@pytest.mark.docs
def test_export_without_summary(
    client_app,
    authenticated_user,
    meeting,
    bbb_getRecordings_response,
    docs_authorization,
    docs_client,
):
    """A recording without Markdown summary has nothing to export."""
    start_export(client_app, meeting, recording_id="unknown")

    response = client_app.get("/docs_callback", status=302).follow(status=200)

    assert "Aucun compte rendu à enregistrer dans Docs." in response.text
    docs_client.create_child_document.assert_not_called()


@pytest.mark.docs
@pytest.mark.parametrize("idp_hint", [None, "proconnect-idp"])
def test_push_starts_the_authorization_flow(
    client_app, authenticated_user, meeting, mocker, idp_hint
):
    """Pushing a summary registers the target and asks ProConnect for a token."""
    client_app.app.config["DOCS_IDP_HINT"] = idp_hint
    authorize_redirect = mocker.patch(
        "authlib.integrations.flask_client.apps.FlaskOAuth2App.authorize_redirect",
        return_value="",
    )

    client_app.post(f"/meeting/{meeting.id}/recordings/{RECORDING_ID}/to-docs")

    expected_params = {"idp_hint": idp_hint} if idp_hint else {}
    authorize_redirect.assert_called_once_with(
        client_app.app.config["DOCS_REDIRECT_URI"], **expected_params
    )
    with client_app.session_transaction() as session:
        assert session["docs_push_target"] == {
            "meeting_id": meeting.id,
            "recording_id": RECORDING_ID,
        }


@pytest.mark.docs
def test_push_requires_meeting_ownership(
    client_app, authenticated_user, meeting_1_user_2
):
    """A delegate cannot export a summary to the meeting owner Docs account."""
    client_app.post(
        f"/meeting/{meeting_1_user_2.id}/recordings/{RECORDING_ID}/to-docs",
        status=403,
    )


@pytest.mark.docs
def test_push_refused_to_an_administrator(
    cli_runner, client_app, authenticated_user, meeting_1_user_2
):
    """An administrator would export to their own Docs account, so they may not."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])

    client_app.post(
        f"/meeting/{meeting_1_user_2.id}/recordings/{RECORDING_ID}/to-docs",
        status=403,
    )


@pytest.mark.docs
def test_callback_without_a_pending_export(client_app, authenticated_user):
    """The callback needs an export registered by the push endpoint."""
    client_app.get("/docs_callback", status=400)


@pytest.mark.docs
def test_push_of_an_exported_recording_skips_proconnect(
    client_app, authenticated_user, meeting, mocker
):
    """An already exported summary needs no new authorization round trip."""
    authorize_redirect = mocker.patch(
        "authlib.integrations.flask_client.apps.FlaskOAuth2App.authorize_redirect"
    )
    db.session.add(
        RecordingDocument(
            meeting=meeting, recording_id=RECORDING_ID, document_id="child-id"
        )
    )
    db.session.commit()

    response = client_app.post(
        f"/meeting/{meeting.id}/recordings/{RECORDING_ID}/to-docs", status=302
    )

    authorize_redirect.assert_not_called()
    assert f"meeting/recordings/{meeting.id}" in response.location


@pytest.mark.docs
def test_recordings_page_links_to_an_exported_summary(
    client_app,
    authenticated_user,
    meeting,
    bbb_getRecordings_ai_summary,
):
    """The recordings page links to Docs instead of offering the export again."""
    response = client_app.get(f"/meeting/recordings/{meeting.id}", status=200)
    assert "Enregistrer dans Docs" in response.text
    assert "Ouvrir dans Docs" not in response.text

    db.session.add(
        RecordingDocument(
            meeting=meeting, recording_id=RECORDING_ID, document_id="child-id"
        )
    )
    db.session.commit()

    response = client_app.get(f"/meeting/recordings/{meeting.id}", status=200)
    assert "Enregistrer dans Docs" not in response.text
    assert "https://docs.test/docs/child-id/" in response.text
