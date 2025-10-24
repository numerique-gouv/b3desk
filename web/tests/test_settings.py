import pytest
from b3desk.settings import MainSettings


def test_list_of_strings_type(configuration):
    """Test that comma-separated string is parsed into list of strings."""
    configuration["OIDC_SCOPES"] = "openid, profile, ect.scope.cv"
    configuration["OIDC_ATTENDEE_SCOPES"] = "openid, profile, ect.scope.cv"

    config_obj = MainSettings.model_validate(configuration)

    assert config_obj.OIDC_SCOPES == ["openid", "profile", "ect.scope.cv"]
    assert config_obj.OIDC_ATTENDEE_SCOPES == ["openid", "profile", "ect.scope.cv"]


def test_enable_sip_true_with_and_without_private_key_home_page(
    client_app,
):
    """Test that missing private key shows error on home page when SIP is enabled."""
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
    """Test that missing private key shows error on welcome page when SIP is enabled."""
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


def test_sip_settings_raised_error_messages_without_fqdn_and_private_key(configuration):
    """Test settings raised error only on FQDN SIP server."""
    configuration["ENABLE_SIP"] = True
    configuration["FQDN_SIP_SERVER"] = None
    configuration["PRIVATE_KEY"] = None

    with pytest.raises(
        ValueError,
        match="FQDN_SIP_SERVER configuration required when enabling SIPMediaGW",
    ):
        MainSettings.model_validate(configuration)


def test_sip_settings_raised_error_messages_without_private_key(configuration):
    """Test settings raised error only on private key."""
    configuration["ENABLE_SIP"] = True
    configuration["FQDN_SIP_SERVER"] = "000.000.000.00"
    configuration["PRIVATE_KEY"] = None

    with pytest.raises(
        ValueError, match="PRIVATE_KEY configuration required when enabling SIPMediaGW"
    ):
        MainSettings.model_validate(configuration)


def test_sip_settings_raised_no_error_with_sip_disabled(configuration):
    """Test settings raised no error when sip is disabled."""
    configuration["ENABLE_SIP"] = False
    configuration["FQDN_SIP_SERVER"] = None
    configuration["PRIVATE_KEY"] = None

    MainSettings.model_validate(configuration)


def test_sip_settings_correctly_completed(configuration):
    """Test settings raised no error when correctly completed."""
    configuration["ENABLE_SIP"] = True
    configuration["FQDN_SIP_SERVER"] = "000.000.000.00"
    configuration["PRIVATE_KEY"] = "very_private_key"

    MainSettings.model_validate(configuration)
