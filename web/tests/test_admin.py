import json
from datetime import date
from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
from b3desk.commands import bp
from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import assign_unique_codes
from b3desk.models.users import User
from flask import url_for


def test_admin_can_enter_admin_page(cli_runner, user, client_app, authenticated_user):
    """Test admin can enter admin page."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/home").follow()
    assert "Admin" in res.text
    client_app.get("/admin/home", status=200)


def test_user_cannot_enter_admin_page(cli_runner, user, client_app, authenticated_user):
    """Test user non admin cannot enter admin page."""
    res = client_app.get("/home").follow()
    assert "Admin" not in res.text
    client_app.get("/admin/home", status=403)


def test_admin_page_display_all_users(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test admin page list all users."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/users", status=200)
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("charlie@domain.tld") == 1


def test_research_bar_with_letters_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test research bar in user list with 'ber'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/users", status=200)
    form = res.form
    form["search"] = "ber"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("charlie@domain.tld") == 0


def test_research_bar_with_digit_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test research bar in user list with '1'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/users", status=200)
    form = res.form
    form["search"] = "1"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("berenice@domain.tld") == 0
    assert res.text.count("charlie@domain.tld") == 0


def test_research_bar_with_no_result_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test research bar in user list with 'zzzzzzzzzzzzzzzzz'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/users", status=200)
    form = res.form
    form["search"] = "zzzzzzzzzzzzzzzzz"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 0
    assert res.text.count("charlie@domain.tld") == 0
    assert res.text.count("Aucun utilisateur ne correspond à cette recherche.") == 1


def test_research_bar_is_kept_through_pagination_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user, mocker
):
    """The search criteria must survive when navigating to another page."""
    # 'li' matches Alice (page 1) and Charlie (page 2), but not Berenice.
    mocker.patch("b3desk.endpoints.admin.PER_PAGE", 1)
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/users?search=li&page=2", status=200)
    assert res.text.count("charlie@domain.tld") == 1
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 0


def test_admin_can_read_user_infos_with_no_meeting(
    cli_runner, user, user_2, client_app, authenticated_user
):
    """Test read user infos for a user without meeting created."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/user/2", status=200)
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count('fr-badge fr-badge--error">Non</p>') == 2
    assert "Berenice Cooler n'a pas créé de réunion." in res.text


def test_admin_can_read_user_infos_with_meeting(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test read user infos for a user having meetings."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/user/1", status=200)
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("Liste des réunions déléguées") == 1
    assert res.text.count("922222222") == 1
    assert res.text.count("511111111") == 1
    assert res.text.count("911111111") == 1
    assert res.text.count("911111112") == 1
    assert res.text.count("911111113") == 1
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 1


def test_research_bar_with_letters_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test admin page list all meetings."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "del"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 0
    assert res.text.count("922222222") == 1
    assert res.text.count("511111111") == 0
    assert res.text.count("911111111") == 0
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0


def test_research_bar_with_digit_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test research bar in meeting list with '1'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "1"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 0
    assert res.text.count("922222222") == 0
    assert res.text.count("511111111") == 0
    assert res.text.count("911111111") == 1
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0


def test_research_bar_with_visio_code_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test research bar in meeting list with '511111111'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "511111111"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 1
    assert res.text.count("922222222") == 0
    assert res.text.count("511111111") == 2
    assert res.text.count("911111111") == 0
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0


def test_research_bar_with_no_result_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test research bar in meeting list with 'zzzzzzzzzzzzzzzzz'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "zzzzzzzzzzzzzzzzz"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 0
    assert res.text.count("922222222") == 0
    assert res.text.count("511111111") == 0
    assert res.text.count("911111111") == 0
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0
    assert res.text.count("Aucune réunion ne correspond à cette recherche.") == 1


@pytest.fixture()
def mock_meeting_is_not_running(mocker):
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)


def test_admin_can_edit_meeting_for_other_user(
    cli_runner,
    user,
    user_2,
    meeting_1_user_2,
    client_app,
    authenticated_user,
    mock_meeting_is_not_running,
):
    """Test admin can edit meeting owned by an other user."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/meeting/edit/1?admin_mode=True", status=200)
    assert res.template == "meeting/wizard.html"
    res.forms[0]["logoutUrl"] = ""
    res = res.forms[0].submit()
    assert (
        "success",
        "delegated meeting modifications prises en compte",
    ) in res.flashes
    assert res.location == "/admin/meeting/1"


def test_admin_can_create_group(
    cli_runner,
    user,
    client_app,
    authenticated_user,
):
    """Test admin can create group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/create-group", status=200)
    res.form["name"] = "Group 1"
    res.form["enable_sip"] = None
    res.form["enable_file_sharing"] = None
    res.form["enable_transcription"] = None
    res = res.form.submit()
    assert (
        "success",
        "Group 1 a bien été créé(e)",
    ) in res.flashes


def test_create_group_have_a_condition_on_sip(
    cli_runner,
    user,
    client_app,
    authenticated_user,
):
    """Test creation group have a condition on enable sip parameter."""
    client_app.app.config["FQDN_SIP_SERVER"] = None
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/create-group", status=200)
    assert "disabled" in res.form["enable_sip"].attrs


def test_admin_cannot_create_group_with_existing_name(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test group name is a unique value."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/create-group", status=200)
    res.form["name"] = "Group 1"
    res.form["enable_sip"] = None
    res.form["enable_file_sharing"] = None
    res.form["enable_transcription"] = None
    res = res.form.submit()
    assert "Ce nom est déjà utilisé." in res.text
    assert len(Group.query.all()) == 1


def test_admin_can_display_groups(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test admin can display groups."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/groups", status=200)
    assert "Group 1" in res.text


def test_admin_can_add_member_in_group(
    cli_runner, user, client_app, authenticated_user, group, caplog
):
    """Test admin can add a user in a group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/add-group-members/1/1", status=200)
    assert "1 membre" in res.text
    assert len(group.members) == 1
    assert ("success", "L'utilisateur a été ajouté au groupe") in res.flashes
    assert "alice@domain.tld became member of group 1 Group 1" in caplog.text


def test_admin_cannot_add_member_already_in_group(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test admin cannot add a user already in a group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/add-group-members/1/1", status=200)
    res = client_app.get("/admin/add-group-members/1/1", status=200)
    assert ("error", "L'utilisateur est déjà dans le groupe") in res.flashes
    assert "1 membre" in res.text
    assert len(group.members) == 1


def test_admin_can_remove_member_from_group(
    cli_runner, user, client_app, authenticated_user, group, caplog
):
    """Test admin can remove member from group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/add-group-members/1/1", status=200)
    res = client_app.get("/admin/manage-group-members/1/1", status=200)
    assert ("success", "L'utilisateur a été retiré du groupe") in res.flashes
    assert "alice@domain.tld member removed from group 1 Group 1" in caplog.text


def test_admin_can_read_information_removing_non_member_user(
    cli_runner, user, user_2, client_app, authenticated_user, group
):
    """Test admin can read inforamtion removing non member user."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/manage-group-members/1", status=200)
    res.form["search"] = "alice@domain.tld"
    res = res.form.submit()
    res = client_app.get("/admin/manage-group-members/1/2", status=200)
    assert ("error", "L'utilisateur ne fait pas partie du groupe") in res.flashes


def test_admin_can_read_group_infos_before_confirm_group_removing(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test admin can read group infos before confirm group removing."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/delete-group/1", status=200)
    assert res.template == "admin/delete_group.html"


def test_research_bar_with_no_result_in_group_list_in_admin_page(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test search with no result in groups."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/groups", status=200)
    res.form["search"] = "zzz"
    res = res.form.submit()
    assert "Aucun groupe ne correspond à cette recherche." in res.text


def test_research_bar_with_digit_in_group_list_in_admin_page(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test search with digit in groups."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/groups", status=200)
    res.form["search"] = "1"
    res = res.form.submit()
    assert "Group 1" in res.text


def test_research_bar_with_letters_in_group_list_in_admin_page(
    cli_runner, user, client_app, authenticated_user, group
):
    """Test search with letters in groups."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/groups", status=200)
    res.form["search"] = "gro"
    res = res.form.submit()
    assert "Group 1" in res.text


def test_admin_can_remove_group(
    cli_runner, user, client_app, authenticated_user, group, caplog
):
    """Test admin can remove group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/confirm-delete-group/1", status=302)
    assert ("success", "Le groupe a été supprimé") in res.flashes
    assert "Groupe 1 Group 1 deleted" in caplog.text
    groups = db.session.scalars(db.select(Group)).all()
    assert len(groups) == 0


def test_admin_can_edit_group(
    cli_runner, user, client_app, authenticated_user, group, caplog
):
    """Test admin can edit group."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/edit-group/1", status=200)
    res.form["name"] = "Group 2"
    res.form["enable_sip"] = None
    res.form["enable_file_sharing"] = None
    res.form["enable_transcription"] = None
    res.form.submit()
    assert (
        "Group Group 2 1 was updated by alice@domain.tld. Updated fields : {'name': 'Group 2', 'enable_sip': None, 'enable_file_sharing': None, 'enable_transcription': None}"
        in caplog.text
    )
    group = db.session.get(Group, 1)
    assert group.name == "Group 2"


def test_edit_group_invalid_form(cli_runner, client_app, authenticated_user, group):
    """Test group edition form dipsplay message if not validated."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get(f"/admin/edit-group/{group.id}", status=200)
    res.form["name"] = ""
    res = res.form.submit()
    assert res.status_int == 200
    assert ("error", "Le formulaire contient des erreurs") in res.flashes


def test_admin_can_toggledownload_meeting_file_not_owner_meeting(
    cli_runner, client_app, authenticated_user, meeting
):
    """Test admin can toggle download meeting file."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=other_meeting.id,
        owner=other_user,
    )
    db.session.add(meeting_file)
    db.session.commit()

    response = client_app.post(
        url_for(
            "meeting_files.toggledownload",
            meeting=other_meeting,
            meeting_file=meeting_file,
        ),
        params=json.dumps({"value": True}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 200
    assert response.json["id"] == meeting_file.id
    db.session.refresh(meeting_file)
    assert meeting_file.is_downloadable is True


def test_admin_can_delete_meeting_file(
    cli_runner, client_app, authenticated_user, meeting
):
    """Test admin can delete meeting file."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=other_meeting.id,
        owner=other_user,
    )
    db.session.add(meeting_file)
    db.session.commit()
    file_id = meeting_file.id

    response = client_app.post(
        url_for("meeting_files.delete_meeting_file"),
        params=json.dumps({"id": file_id}),
        headers={"Content-Type": "application/json"},
        expect_errors=True,
    )

    assert response.status_int == 200
    assert response.json["id"] == meeting_file.id
    print(response)
    assert not MeetingFiles.query.all()


def test_admin_can_update_recording_name(
    cli_runner, client_app, authenticated_user, bbb_response
):
    """Test admin can update recording name."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])

    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    response = client_app.post(
        f"/meeting/{other_meeting.id}/recordings/recording_id",
        {"name": "First recording"},
        status=302,
    )

    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/updateRecordings"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params["meta_name"] == "First recording"
    assert bbb_params["recordID"] == "recording_id"

    assert f"meeting/recordings/{other_meeting.id}" in response.location


###


def test_admin_can_delete_recordings(
    cli_runner,
    mocker,
    client_app,
    authenticated_user,
    bbb_getRecordings_response,
    caplog,
):
    """Test admin can delete recordings."""
    from b3desk.models.bbb import BBB

    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])

    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)
    recordings = BBB(other_meeting.meetingID).get_recordings()

    assert len(recordings) == 2
    first_recording_id = recordings[0]["recordID"]

    response = client_app.post(
        f"/meeting/{other_meeting.id}/video/delete",
        {"recordID": first_recording_id},
    )

    assert (
        f"Meeting Other meeting {other_meeting.id} record {first_recording_id} was deleted by alice@domain.tld\n"
    ) in caplog.text
    assert ("success", "Vidéo supprimée") in response.flashes


def test_admin_can_open_recordings_page(
    cli_runner,
    client_app,
    authenticated_user,
    mocker,
    bbb_response,
    bbb_getRecordings_response,
):
    """Test admin can open recordings page."""
    from b3desk.models.bbb import BBB

    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])

    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)

    response = client_app.get(f"/meeting/recordings/{other_meeting.id}")
    html = response.body.decode("utf-8")
    assert (
        html.count(
            '<button type="button" class="btn-copy fr-btn fr-btn--primary fr-ml-1v fr-icon-clipboard-line"'
        )
        == 2
    )
    assert len(BBB(other_meeting.meetingID).get_recordings()) == 2


def test_admin_can_read_meeting_infos(
    cli_runner, user, meeting_2_user_2, client_app, authenticated_user
):
    """Test admin can read meeting infos."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meeting/1", status=200)
    assert res.text.count("922222221") == 5
    assert res.text.count("222222221") == 3
    assert res.text.count("Berenice Cooler") == 1


def test_admin_cannot_edit_files_if_meeting_owner_cannot_use_file_sharing(
    cli_runner, client_app, authenticated_user, user_2, meeting_2_user_2, group_2
):
    """Test admin cannot edit meeting files if owner cannot use file sharing."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/add-group-members/1/2", status=200)
    assert user_2.groups[0].name == "Group 2"
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting_2_user_2),
        status=302,
    )
    assert ("warning", "Vous ne pouvez pas modifier cet élément") in res.flashes
