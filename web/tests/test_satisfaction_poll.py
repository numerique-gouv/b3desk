def test_no_satisfaction_poll(client_app, authenticated_user, bbb_response):
    """Test that no satisfaction poll iframe is displayed when URL is not configured."""
    res = client_app.get("/welcome")
    res.mustcontain(no="iframe")


def test_satisfaction_poll_url(client_app, authenticated_user, meeting, bbb_response):
    """Test that satisfaction poll iframe is displayed with configured URL."""
    client_app.app.config["SATISFACTION_POLL_URL"] = "https://poll.test"
    res = client_app.get("/welcome")
    res.mustcontain("iframe")
    res.mustcontain("https://poll.test")
