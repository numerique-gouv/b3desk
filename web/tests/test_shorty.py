def test_shorty_mode_with_mailto_links(client_app, authenticated_user, meeting):
    client_app.app.config["SHORTY"] = True
    client_app.app.config["MAILTO_LINKS"] = True

    res = client_app.get("/welcome", status=200)
    assert res.text.count('href="mailto:_@_?') == 2
