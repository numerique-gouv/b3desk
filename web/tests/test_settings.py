from b3desk.settings import MainSettings


def test_list_of_strings_type(configuration):
    configuration["OIDC_SCOPES"] = "openid, profile, ect.scope.cv"
    configuration["OIDC_ATTENDEE_SCOPES"] = "openid, profile, ect.scope.cv"

    config_obj = MainSettings.model_validate(configuration)

    assert config_obj.OIDC_SCOPES == ["openid", "profile", "ect.scope.cv"]
    assert config_obj.OIDC_ATTENDEE_SCOPES == ["openid", "profile", "ect.scope.cv"]


def test_enable_sip_true_with_and_without_private_key_home_page(
    client_app,
):
    response = client_app.get("/", status=302)
    assert "/home" in response.location
    assert (
        "error",
        "La clé privée n'a pas été configurée dans les paramètres B3Desk pour sécuriser la connexion SIP",
    ) not in response.flashes
    client_app.app.config["PRIVATE_KEY"] = None
    response = client_app.get("/home", status=200)
    assert (
        "error",
        "La clé privée n'a pas été configurée dans les paramètres B3Desk pour sécuriser la connexion SIPMediaGW",
    ) in response.flashes


def test_enable_sip_true_with_and_without_private_key_welcome_page(
    client_app,
    authenticated_user,
):
    response = client_app.get("/", status=302)
    assert "/welcome" in response.location
    assert (
        "error",
        "La clé privée n'a pas été configurée dans les paramètres B3Desk pour sécuriser la connexion SIP",
    ) not in response.flashes

    client_app.app.config["PRIVATE_KEY"] = None
    response = client_app.get("/welcome", status=200)
    assert (
        "error",
        "La clé privée n'a pas été configurée dans les paramètres B3Desk pour sécuriser la connexion SIPMediaGW",
    ) in response.flashes
