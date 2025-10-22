import sys
from unittest.mock import Mock

import pytest
from b3desk import create_app
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


def test_log_config_with_ini_file(configuration, monkeypatch, tmp_path):
    """Test LOG_CONFIG parameter with an INI configuration file."""
    ini_file = tmp_path / "logging.ini"
    ini_file.write_text("""[loggers]
keys=root,b3desk

[handlers]
keys=wsgi,b3desk

[formatters]
keys=default

[logger_root]
level=INFO
handlers=wsgi

[logger_b3desk]
level=INFO
handlers=b3desk
qualname=b3desk

[handler_wsgi]
class=logging.handlers.WatchedFileHandler
level=NOTSET
formatter=default
args=('/var/log/wsgi.log',)

[handler_b3desk]
class=logging.handlers.WatchedFileHandler
level=NOTSET
formatter=default
args=('/var/log/b3desk.log',)

[formatter_default]
format=[%(asctime)s] %(levelname)s in %(module)s: %(message)s
""")

    configuration["LOG_CONFIG"] = str(ini_file)
    config_obj = MainSettings.model_validate(configuration)
    assert config_obj.LOG_CONFIG == ini_file

    mock_fileConfig = Mock()
    monkeypatch.setattr("b3desk.fileConfig", mock_fileConfig)

    create_app(configuration)
    mock_fileConfig.assert_called_once_with(ini_file, disable_existing_loggers=False)


@pytest.mark.skipif(
    sys.version_info < (3, 11), reason="Needs Python 3.11 for toml config"
)
def test_log_config_with_toml_file(configuration, monkeypatch, tmp_path):
    """Test LOG_CONFIG parameter with an INI configuration file."""
    toml_file = tmp_path / "logging.toml"
    toml_file.write_text("""version = 1

[formatters.default]
format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

[handlers.wsgi]
class = "logging.handlers.WatchedFileHandler"
filename = "/var/log/wsgi.log"
formatter = "default"

[handlers.b3desk]
class = "logging.handlers.WatchedFileHandler"
filename = "/var/log/b3desk.log"
formatter = "default"

[loggers.b3desk]
level = "INFO"
handlers = ["b3desk"]

[root]
level = "INFO"
handlers = ["wsgi"]
""")

    configuration["LOG_CONFIG"] = str(toml_file)
    config_obj = MainSettings.model_validate(configuration)
    assert config_obj.LOG_CONFIG == toml_file

    mock_dictConfig = Mock()
    monkeypatch.setattr("b3desk.dictConfig", mock_dictConfig)

    create_app(configuration)
    mock_dictConfig.assert_called_once()


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
