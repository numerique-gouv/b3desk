def test_join_meeting_with_wrong_visio_code_until_captcha(
    client_app, meeting, visio_code_session
):
    def fill_and_submit_visio_code():
        response = client_app.get("/home", status=200)
        response.forms[0]["visio_code"] = "123456789"
        response = response.forms[0].submit()
        assert ("error", "Le code de connexion saisi est erroné") in response.flashes
        return response

    for i in range(5):
        response = fill_and_submit_visio_code()
        assert ("error", "Erreur Captcha : rechargez la page") not in response.flashes
    response = fill_and_submit_visio_code()
    response = response.follow()
    response.mustcontain("captcha-container")

    response = client_app.get("/home", status=200)
    response.mustcontain("captcha-container")
    response.forms[0]["visio_code"] = "911111111"
    response = response.forms[0].submit()
    response.mustcontain("Rejoindre le séminaire")
    response = fill_and_submit_visio_code()
    assert ("error", "Erreur Captcha : rechargez la page") not in response.flashes
