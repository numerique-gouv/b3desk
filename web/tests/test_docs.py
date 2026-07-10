from b3desk.docs import create_document


def test_create_document(app, mocker):
    """create_document posts the file to the Docs external API with the bearer token."""
    app.config["DOCS_API_URL"] = "https://docs.example"
    post = mocker.patch("b3desk.docs.requests.post")
    post.return_value.json.return_value = {"id": "abc"}

    with app.app_context():
        result = create_document("access-tok", "Resume.md", b"# hi")

    assert result == {"id": "abc"}
    args, kwargs = post.call_args
    assert args[0] == "https://docs.example/external_api/v1.0/documents/"
    assert kwargs["headers"]["Authorization"] == "Bearer access-tok"
    filename, content, content_type = kwargs["files"]["file"]
    assert (filename, content, content_type) == ("Resume.md", b"# hi", "text/markdown")
    post.return_value.raise_for_status.assert_called_once()


def test_docs_routes_absent_when_disabled(app):
    """The Docs blueprint is not registered when the feature is disabled."""
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "docs.push_recording_to_docs" not in endpoints
