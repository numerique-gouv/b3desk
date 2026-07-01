import pytest
from b3desk.commands import bp
from b3desk.join import create_bbb_meeting


def test_add_group_members_page_displays_users(
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


def test_add_group_members_page_filters_by_search(
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
    res = client_app.get("/admin/add-group-members/2/2", status=200)
    res = client_app.get("/admin/add-group-members/3/2", status=200)
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
    res = client_app.get("/admin/add-group-members/2/2", status=200)
    res = client_app.get("/admin/add-group-members/3/2", status=200)
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
    res = client_app.get("/admin/add-group-members/1/1", status=200)
    res = client_app.get("/admin/add-group-members/2/2", status=200)
    res = client_app.get("/admin/add-group-members/3/3", status=200)
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
    res = client_app.get("/admin/add-group-members/1/1", status=200)
    res = client_app.get("/admin/add-group-members/2/2", status=200)
    res = client_app.get("/admin/add-group-members/3/3", status=200)
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


def test_can_use_ai_summary_returns_true_when_group_enables_it(client_app, user, group):
    user.groups.append(group)  # group: enable_ai_summary=True
    assert user.can_use_ai_summary is True


def test_can_use_ai_summary_returns_false_when_all_groups_disable_it(
    client_app, user, group_2
):
    user.groups.append(group_2)  # group_2: enable_ai_summary=False
    assert user.can_use_ai_summary is False


def test_can_use_ai_summary_falls_back_to_config_when_group_has_none(
    client_app, user, group_3
):
    client_app.app.config["ENABLE_AI_SUMMARY"] = True
    user.groups.append(group_3)  # group_3: enable_ai_summary=None
    assert user.can_use_ai_summary is True


@pytest.fixture()
def mock_meeting_is_not_running(mocker):
    """Mock meeting.bbb.is_running() to return False."""
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)


def test_meeting_with_ai_summary_but_owner_lost_authorisation(
    cli_runner,
    client_app,
    user,
    meeting,
    group,
    group_2,
    authenticated_user,
    mock_meeting_is_not_running,
    bbb_response,
):
    """Test when owner loses ai-summary authorization, ai_summary is disabled on their meetings before launch."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    client_app.get("/admin/add-group-members/1/1", status=200)
    client_app.get("/admin/add-group-members/2/1", status=200)
    assert user.can_use_ai_summary is True
    meeting.ai_summary = True
    client_app.get("/admin/manage-group-members/1/1", status=200)
    create_bbb_meeting(meeting, meeting.owner)
    assert meeting.ai_summary is False
    assert user.can_use_ai_summary is False
