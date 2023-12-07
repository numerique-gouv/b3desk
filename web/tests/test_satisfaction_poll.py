def test_no_satisfaction_poll(client_app, authenticated_user, bbb_response):
    res = client_app.get("/welcome")
    res.mustcontain(no="iframe")


def test_satisfaction_poll_url(client_app, authenticated_user, meeting, bbb_response):
    client_app.app.config["SATISFACTION_POLL_URL"] = "https://poll.example.org"
    res = client_app.get("/welcome")
    res.mustcontain("iframe")
    res.mustcontain("https://poll.example.org")
