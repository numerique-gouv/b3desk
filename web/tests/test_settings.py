from b3desk.settings import MainSettings


def test_list_of_strings_type(configuration):
    configuration["OIDC_SCOPES"] = "openid, profile, ect.scope.cv"
    configuration["OIDC_ATTENDEE_SCOPES"] = "openid, profile, ect.scope.cv"

    config_obj = MainSettings.model_validate(configuration)

    assert config_obj.OIDC_SCOPES == ["openid", "profile", "ect.scope.cv"]
    assert config_obj.OIDC_ATTENDEE_SCOPES == ["openid", "profile", "ect.scope.cv"]
