from b3desk.commands import bp


def test_add_group_members_displays_users(
    cli_runner,
    client_app,
    user,
    group,
    authenticated_user,
):
    """Test that add group members page renders with the user list."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get(f"/admin/add-group-members/{group.id}", status=200)
    assert user.email in res.text


def test_add_group_members_filters_by_search(
    cli_runner,
    client_app,
    user,
    user_2,
    group,
    authenticated_user,
):
    """Test that add group members page filters users by search term."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get(
        f"/admin/add-group-members/{group.id}?search={user.email}", status=200
    )
    assert user.email in res.text
    assert user_2.email not in res.text


def test_group_infos_page_displays_group_details(
    cli_runner,
    client_app,
    user,
    group,
    authenticated_user,
):
    """Test that group infos page renders with the correct group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get(f"/admin/group/{group.id}", status=200)
    assert group.name in res.text


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
    res = client_app.post("/admin/add-group-members/2", {"user_ids": [2]}, status=302)
    res = client_app.post("/admin/add-group-members/3", {"user_ids": [2]}, status=302)
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
    res = client_app.post("/admin/add-group-members/2", {"user_ids": [2]}, status=302)
    res = client_app.post("/admin/add-group-members/3", {"user_ids": [2]}, status=302)
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
    res = client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    res = client_app.post("/admin/add-group-members/2", {"user_ids": [2]}, status=302)
    res = client_app.post("/admin/add-group-members/3", {"user_ids": [3]}, status=302)
    assert user.groups[0].name == "Group 1"
    assert user.groups[0].enable_file_sharing
    assert user_2.groups[0].name == "Group 2"
    assert not user_2.groups[0].enable_file_sharing
    assert user_3.groups[0].name == "Group 3"
    assert user_3.groups[0].enable_file_sharing is None
    res = client_app.get("/welcome")
    assert res.context["meetings"][2].visio_code == "911111111"
    assert res.context["meetings"][2].owner.can_use_file_sharing
    assert res.context["meetings"][1].visio_code == "922222222"
    assert not res.context["meetings"][1].owner.can_use_file_sharing
    assert res.context["meetings"][0].visio_code == "933333333"
    assert res.context["meetings"][0].owner.can_use_file_sharing


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
    res = client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    res = client_app.post("/admin/add-group-members/2", {"user_ids": [2]}, status=302)
    res = client_app.post("/admin/add-group-members/3", {"user_ids": [3]}, status=302)
    assert user.groups[0].name == "Group 1"
    assert user.groups[0].enable_file_sharing
    assert user_2.groups[0].name == "Group 2"
    assert not user_2.groups[0].enable_file_sharing
    assert user_3.groups[0].name == "Group 3"
    assert user_3.groups[0].enable_file_sharing is None
    res = client_app.get("/welcome")
    assert res.context["meetings"][2].visio_code == "911111111"
    assert res.context["meetings"][2].owner.can_use_file_sharing
    assert res.context["meetings"][1].visio_code == "922222222"
    assert not res.context["meetings"][1].owner.can_use_file_sharing
    assert res.context["meetings"][0].visio_code == "933333333"
    assert not res.context["meetings"][0].owner.can_use_file_sharing


def test_admin_can_add_multiple_users_at_once_in_a_group(
    cli_runner, client_app, user, user_2, user_3, group, authenticated_user, caplog
):
    """Test admin can add multiple users at once in a group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post(
        "/admin/add-group-members/1", {"user_ids": [1, 2, 3]}, status=302
    )
    assert ("success", "3 membre(s) ajouté(s) au groupe") in res.flashes
    assert "alice@domain.tld became member of group 1 Group 1" in caplog.text
    assert "berenice@domain.tld became member of group 1 Group 1" in caplog.text
    assert "charlie@domain.tld became member of group 1 Group 1" in caplog.text


def test_message_displayed_if_admin_did_not_selected_at_least_one_user(
    cli_runner, client_app, user, group, authenticated_user, caplog
):
    """Test a message is displayed if tha admin has not selected a user to add."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post("/admin/add-group-members/1", {"user_ids": []}, status=302)
    assert ("message", "Vous n'avez pas sélectionné d'utilisateur") in res.flashes


def test_admin_can_add_multiple_users_filtered_with_search(
    cli_runner, client_app, user, user_2, user_3, group, authenticated_user, caplog
):
    """Test admin can add multiple users filtered with search."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post(
        "/admin/add-group-members/1?search=%40ladomain.tld&select_all=1"
    )
    assert ("success", "3 membre(s) ajouté(s) au groupe") in res.flashes
    assert "alice@domain.tld became member of group 1 Group 1" in caplog.text
    assert "berenice@domain.tld became member of group 1 Group 1" in caplog.text
    assert "charlie@domain.tld became member of group 1 Group 1" in caplog.text
