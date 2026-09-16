from b3desk.commands import bp
from b3desk.join import create_bbb_meeting
from b3desk.models import db


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


def test_add_group_members_excludes_existing_members(
    cli_runner,
    client_app,
    user,
    user_2,
    group,
    authenticated_user,
):
    """Test that users already in the group don't appear in the add members list."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    user_2.groups.append(group)
    db.session.commit()

    res = client_app.get(f"/admin/add-group-members/{group.id}", status=200)

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
    user.admin = True
    user.admin = True
    group.members.append(user)
    group_2.members.append(user_2)
    group_3.members.append(user_3)
    group.academic_code.append("domain.tld")
    db.session.commit()
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
    user.admin = True
    group.members.append(user)
    group_2.members.append(user_2)
    group_3.members.append(user_3)
    group.academic_code.append("domain.tld")
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
    assert ("success", "3 membres ajoutés au groupe") in res.flashes
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


def test_non_numeric_user_id_is_ignored(
    cli_runner, client_app, user, group, authenticated_user
):
    """Test a malformed user id does not raise a server error."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post(
        "/admin/add-group-members/1", {"user_ids": ["oops"]}, status=302
    )
    assert ("message", "Vous n'avez pas sélectionné d'utilisateur") in res.flashes
    assert not group.members


def test_admin_can_add_multiple_users_filtered_with_search(
    cli_runner, client_app, user, user_2, user_3, group, authenticated_user, caplog
):
    """Test admin adds every user matching the search, and only those."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post(
        "/admin/add-group-members/1", {"search": "ber", "select_all": "1"}, status=302
    )
    assert ("success", "1 membre ajouté au groupe") in res.flashes
    assert [member.email for member in group.members] == ["berenice@domain.tld"]
    assert "berenice@domain.tld became member of group 1 Group 1" in caplog.text


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
    """When the owner loses ai-summary authorisation, launching the meeting keeps the stored preference while ai_summary_enabled reflects the loss."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    group.academic_code.append("domain.tld")
    group_2.academic_code.append("domain.tld")
    db.session.commit()
    client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    client_app.post("/admin/add-group-members/2", {"user_ids": [1]}, status=302)
    assert user.can_use_ai_summary is True
    meeting.ai_summary = True
    assert meeting.ai_summary_enabled is True
    client_app.post("/admin/manage-group-members/1/1", status=302)
    create_bbb_meeting(meeting, meeting.owner)
    assert user.can_use_ai_summary is False
    assert meeting.ai_summary is True
    assert meeting.ai_summary_enabled is False


def test_create_bbb_meeting_file_sharing_follows_owner_not_launcher(
    cli_runner,
    client_app,
    user,
    user_2,
    meeting,
    group,
    group_2,
    authenticated_user,
    mock_meeting_is_not_running,
    mocker,
):
    """In delegation, the BBB room file-sharing flag follows the owner's ability, not the launcher's."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    # Alice's domain matches Group 2 so automatic_group_affiliation doesn't
    # remove her from it on the second request below; Group 1 must stay
    # without a matching domain so she isn't auto-added there too.
    group_2.academic_code.append("domain.tld")
    db.session.commit()
    # Owner alice (id 1) in Group 2: file sharing disabled.
    client_app.post("/admin/add-group-members/2", {"user_ids": [1]}, status=302)
    # Launcher berenice (id 2) in Group 1: file sharing enabled.
    client_app.post("/admin/add-group-members/1", {"user_ids": [2]}, status=302)
    assert meeting.owner_id == user.id
    assert user.can_use_file_sharing is False
    assert user_2.can_use_file_sharing is True

    create = mocker.patch(
        "b3desk.models.bbb.BBB.create",
        return_value={"returncode": "SUCCESS", "voiceBridge": meeting.voiceBridge},
    )
    create_bbb_meeting(meeting, user_2)
    assert create.call_args.kwargs["file_sharing"] is False


def test_automatic_affiliation_with_academic_domain(user_2, group):
    """Test user not in group become member if is from academic domain list."""
    group.academic_code = ["domain.tld"]
    db.session.commit()
    assert group.members == []
    user_2.automatic_group_affiliation()
    assert group.members == [user_2]


def test_automatic_affiliation_with_academic_domain_and_user_in_excluded_users(
    user_2, group
):
    """Test excluded user does not become member even if is from academic domain list."""
    group.academic_code = ["domain.tld"]
    group.excluded_users.append(user_2)
    db.session.commit()
    user_2.automatic_group_affiliation()
    assert group.members == []


def test_automatic_removing_from_group_if_in_excluded_users(user_2, group):
    """Test user in group is automaticly remove if is excluded."""
    group.members.append(user_2)
    group.excluded_users.append(user_2)
    group.academic_code.append("domain.tld")
    db.session.commit()
    assert user_2 in db.session.execute(group.get_all_exclude_users).scalars().all()
    user_2.automatic_group_affiliation()
    assert group.members == []


def test_automatic_removing_from_group_if_not_in_academic_list(user_2, group):
    """Test user in group is automaticly remove if is not in academic list excluded."""
    assert not group.members
    group.academic_code.append("domain.tld")
    db.session.commit()
    user_2.automatic_group_affiliation()
    assert user_2 in group.members
    group.academic_code.remove("domain.tld")
    db.session.commit()
    user_2.automatic_group_affiliation()
    assert not group.members


def test_admin_can_add_domain_in_group(client_app, group, user, authenticated_user):
    """Test admin can add academic domain in group."""
    user.admin = True
    db.session.commit()
    res = client_app.get("/admin/academic-domain/1", status=200)
    form = res.form
    form["academic_domain"] = "domain.tld"
    form.submit()
    assert group.academic_code == ["domain.tld"]
    client_app.get("/welcome")
    assert group.members == [user]


def test_add_domain_in_group_with_form_error(
    client_app, group, user, authenticated_user
):
    """Test academic domain form display error message."""
    user.admin = True
    db.session.commit()
    res = client_app.get("/admin/academic-domain/1", status=200)
    form = res.form
    form["academic_domain"] = ""
    res = form.submit()
    assert ("error", "Le formulaire contient des erreurs") in res.flashes


def test_add_domain_already_in_group(client_app, group, user, authenticated_user):
    """Test admin cannot add academic domain already in group."""
    user.admin = True
    group.academic_code.append("domain.tld")
    db.session.commit()
    res = client_app.get("/admin/academic-domain/1", status=200)
    form = res.form
    form["academic_domain"] = "domain.tld"
    res = form.submit()
    assert (
        "error",
        "domain.tld est déjà dans la liste du groupe Group 1",
    ) in res.flashes


def test_admin_can_remove_domain_in_group(client_app, group, user, authenticated_user):
    """Test admin can remove academic domain in group."""
    user.admin = True
    group.academic_code.append("domain.tld")
    db.session.commit()
    assert group.academic_code == ["domain.tld"]
    client_app.get(
        "/admin/remove-academic-domain/1", params={"domain": "domain.tld"}, status=200
    )
    assert group.academic_code == []


def test_admin_can_add_excluded_user_in_group(
    client_app, group, user, user_2, authenticated_user
):
    """Test admin can add excluded in group."""
    user.admin = True
    db.session.commit()
    res = client_app.get("/admin/excluded-users/1", status=200)
    form = res.form
    form["search"] = user_2.email
    form.submit()
    assert group.excluded_users == [user_2]


def test_add_excluded_user_in_group_with_form_error(
    client_app, group, user, user_2, authenticated_user
):
    """Test excluded user form display error message."""
    user.admin = True
    db.session.commit()
    res = client_app.get("/admin/excluded-users/1", status=200)
    form = res.form
    form["search"] = ""
    res = form.submit()
    assert ("error", "Le formulaire contient des erreurs") in res.flashes


def test_admin_cannot_add_excluded_user_already_excluded(
    client_app, group, user, user_2, authenticated_user
):
    """Test admin cannot add excluded user already excluded."""
    user.admin = True
    group.excluded_users.append(user_2)
    db.session.commit()
    res = client_app.get("/admin/excluded-users/1", status=200)
    form = res.form
    form["search"] = user_2.email
    res = form.submit()
    assert ("error", "L'utilisateur est déjà pas dans la liste") in res.flashes


def test_admin_remove_excluded_user_in_group(
    client_app, group, user, user_2, authenticated_user
):
    """Test admin can remove excluded user in group."""
    user.admin = True
    group.excluded_users.append(user_2)
    db.session.commit()
    assert group.excluded_users == [user_2]
    client_app.get("/admin/excluded-users/1/2", status=200)
    assert group.excluded_users == []


def test_admin_cannot_remove_not_excluded_user_from_excluded_users_list(
    client_app, group, user, user_2, authenticated_user
):
    """Test admin cannot remove not excluded user from excluded users list."""
    user.admin = True
    db.session.commit()
    res = client_app.get("/admin/excluded-users/1/2", status=200)
    assert ("error", "L'utilisateur n'est pas dans la liste") in res.flashes
