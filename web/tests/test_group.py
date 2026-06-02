from b3desk.commands import bp


def test_api_meetings_for_user_can_use_sip_in_group_enable_sip_and_setting_enable_sip(
    cli_runner,
    client_app,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    iam_token,
    group,
    group_2,
    group_3,
    authenticated_user,
):
    """Test that API returns SIPMediaGW_url if meeting's owner in group 1: enable sip, 2: disable sip, 3: none able sip and settings enable sip."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/manage-group-members/1", status=200)
    res.form["search"] = "alice@domain.tld"
    res = res.form.submit()
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )
    assert (
        res.json["meetings"][0]["SIPMediaGW_url"]
        == res.json["meetings"][0]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][1]["SIPMediaGW_url"]
        == res.json["meetings"][1]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][2]["SIPMediaGW_url"]
        == res.json["meetings"][2]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][3]["SIPMediaGW_url"]
        == res.json["meetings"][3]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert res.json["meetings"][3]["delegate"]


def test_api_meetings_for_delegate_can_use_sip_and_owner_none_able_to_use_sip(
    cli_runner,
    client_app,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    iam_token,
    group,
    group_2,
    group_3,
    authenticated_user,
):
    """Test that API returns not SIPMediaGW_url if meeting's owner in group 2: disable sip, 3: none able sip and settings enable sip."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/manage-group-members/2", status=200)
    res.form["search"] = "berenice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/3", status=200)
    res.form["search"] = "berenice@domain.tld"
    res = res.form.submit()
    assert user_2.groups[0].name == "Group 2"
    assert user_2.groups[1].name == "Group 3"
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )
    assert (
        res.json["meetings"][0]["SIPMediaGW_url"]
        == res.json["meetings"][0]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][1]["SIPMediaGW_url"]
        == res.json["meetings"][1]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][2]["SIPMediaGW_url"]
        == res.json["meetings"][2]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][3]["SIPMediaGW_url"]
        == res.json["meetings"][3]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert res.json["meetings"][3]["delegate"]


def test_api_meetings_for_delegate_can_use_sip_and_owner_cannot(
    cli_runner,
    client_app,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    iam_token,
    group,
    group_2,
    group_3,
    authenticated_user,
):
    """Test that API returns not SIPMediaGW_url if meeting's owner in group 2: disable sip, 3: disable sip and settings enable sip."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/manage-group-members/2", status=200)
    res.form["search"] = "berenice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/3", status=200)
    res.form["search"] = "berenice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/edit-group/3", status=200)
    res.form["enable_sip"] = False
    res.form.submit()
    assert user_2.groups[0].name == "Group 2"
    assert user_2.groups[1].name == "Group 3"
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )
    assert (
        res.json["meetings"][0]["SIPMediaGW_url"]
        == res.json["meetings"][0]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][1]["SIPMediaGW_url"]
        == res.json["meetings"][1]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert (
        res.json["meetings"][2]["SIPMediaGW_url"]
        == res.json["meetings"][2]["visio_code"]
        + "@"
        + client_app.app.config["FQDN_SIP_SERVER"]
    )
    assert "SIPMediaGW_url" not in res.json["meetings"][3]
    assert res.json["meetings"][3]["delegate"]


def test_welcome_page_displays_file_sharing_icon_according_to_owner_ability_with_file_sharing_setting_true(
    cli_runner,
    client_app,
    user,
    user_2,
    user_3,
    meeting,
    meeting_1_user_2,
    meeting_1_user_3,
    iam_token,
    group,
    group_2,
    group_3,
    authenticated_user,
):
    """Test that welcome page displays file sharing icon according to owner ability with file sharing setting True."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/manage-group-members/1", status=200)
    res.form["search"] = "alice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/2", status=200)
    res.form["search"] = "berenice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/3", status=200)
    res.form["search"] = "charlie@domain.tld"
    res = res.form.submit()
    assert user.groups[0].name == "Group 1"
    assert user.groups[0].enable_file_sharing
    assert user_2.groups[0].name == "Group 2"
    assert not user_2.groups[0].enable_file_sharing
    assert user_3.groups[0].name == "Group 3"
    assert user_3.groups[0].enable_file_sharing is None
    res = client_app.get("/welcome")
    assert res.context["meetings"][2].visio_code == "911111111"
    assert res.context["meetings"][2].owner_can_use_file_sharing
    assert res.context["meetings"][1].visio_code == "922222222"
    assert not res.context["meetings"][1].owner_can_use_file_sharing
    assert res.context["meetings"][0].visio_code == "933333333"
    assert res.context["meetings"][0].owner_can_use_file_sharing


def test_welcome_page_displays_file_sharing_icon_according_to_owner_ability_with_file_sharing_setting_false(
    cli_runner,
    client_app,
    user,
    user_2,
    user_3,
    meeting,
    meeting_1_user_2,
    meeting_1_user_3,
    iam_token,
    group,
    group_2,
    group_3,
    authenticated_user,
):
    """Test that welcome page displays file sharing icon according to owner ability with file sharing setting False."""
    client_app.app.config["FILE_SHARING"] = False
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/manage-group-members/1", status=200)
    res.form["search"] = "alice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/2", status=200)
    res.form["search"] = "berenice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/3", status=200)
    res.form["search"] = "charlie@domain.tld"
    res = res.form.submit()
    assert user.groups[0].name == "Group 1"
    assert user.groups[0].enable_file_sharing
    assert user_2.groups[0].name == "Group 2"
    assert not user_2.groups[0].enable_file_sharing
    assert user_3.groups[0].name == "Group 3"
    assert user_3.groups[0].enable_file_sharing is None
    res = client_app.get("/welcome")
    assert res.context["meetings"][2].visio_code == "911111111"
    assert res.context["meetings"][2].owner_can_use_file_sharing
    assert res.context["meetings"][1].visio_code == "922222222"
    assert not res.context["meetings"][1].owner_can_use_file_sharing
    assert res.context["meetings"][0].visio_code == "933333333"
    assert not res.context["meetings"][0].owner_can_use_file_sharing
