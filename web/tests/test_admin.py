import json
from datetime import date
from datetime import datetime
from urllib.parse import parse_qs
from urllib.parse import urlparse

from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import assign_unique_codes
from b3desk.models.users import User
from flask import url_for

from tests.helpers import form_with_action


def test_admin_can_enter_admin_page(user, client_app, authenticated_admin):
    """Test admin can enter admin page."""
    res = client_app.get("/home").follow()
    assert "Admin" in res.text
    client_app.get("/admin/home", status=200)


def test_expired_admin_session_is_not_redirected_to_admin_page(
    client_app, authenticated_admin
):
    """Test an expired admin session shows the public home page."""
    with client_app.session_transaction() as session:
        session["last_authenticated"] = 0
    res = client_app.get("/home", status=200)
    assert res.template == "index.html"
    with client_app.session_transaction() as session:
        assert "admin_userinfo" not in session


def test_admin_is_not_redirected_to_admin_page_with_admin_management_disabled(
    client_app, authenticated_admin
):
    """Test an admin session shows the public home page when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    res = client_app.get("/home", status=200)
    assert res.template == "index.html"


def test_user_cannot_enter_admin_page(cli_runner, user, client_app, authenticated_user):
    """Test user non admin cannot enter admin page."""
    res = client_app.get("/home").follow()
    assert "Admin" not in res.text
    client_app.get("/admin/home", status=403)


def test_admin_page_display_all_users(
    user, user_2, user_3, client_app, authenticated_admin
):
    """Test admin page list all users."""
    res = client_app.get("/admin/users", status=200)
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("charlie@domain.tld") == 1


def test_research_bar_with_letters_in_user_list_in_admin_page(
    user, user_2, user_3, client_app, authenticated_admin
):
    """Test research bar in user list with 'ber'."""
    res = client_app.get("/admin/users", status=200)
    form = res.form
    form["search"] = "ber"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("charlie@domain.tld") == 0


def test_research_bar_with_digit_in_user_list_in_admin_page(
    user, user_2, user_3, client_app, authenticated_admin
):
    """Test research bar in user list with '1'."""
    res = client_app.get("/admin/users", status=200)
    form = res.form
    form["search"] = "1"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("berenice@domain.tld") == 0
    assert res.text.count("charlie@domain.tld") == 0


def test_research_bar_with_no_result_in_user_list_in_admin_page(
    user, user_2, user_3, client_app, authenticated_admin
):
    """Test research bar in user list with 'zzzzzzzzzzzzzzzzz'."""
    res = client_app.get("/admin/users", status=200)
    form = res.form
    form["search"] = "zzzzzzzzzzzzzzzzz"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 0
    assert res.text.count("charlie@domain.tld") == 0
    assert res.text.count("Aucun utilisateur ne correspond à cette recherche.") == 1


def test_research_bar_is_kept_through_pagination_in_user_list_in_admin_page(
    user, user_2, user_3, client_app, authenticated_admin, mocker
):
    """The search criteria must survive when navigating to another page."""
    # 'li' matches Alice (page 1) and Charlie (page 2), but not Berenice.
    mocker.patch("b3desk.endpoints.admin.PER_PAGE", 1)
    res = client_app.get("/admin/users?search=li&page=2", status=200)
    assert res.text.count("charlie@domain.tld") == 1
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 0


def test_admin_can_read_user_infos_with_no_meeting(
    user, user_2, client_app, authenticated_admin
):
    """Test read user infos for a user without meeting created."""
    res = client_app.get("/admin/user/2", status=200)
    assert res.text.count("berenice@domain.tld") == 1
    assert "<em>Berenice Cooler</em> n'a pas créé de réunion." in res.text


def test_admin_can_read_user_infos_with_meeting(
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_admin,
):
    """Test read user infos for a user having meetings."""
    res = client_app.get("/admin/user/1", status=200)
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("Liste des réunions déléguées") == 1
    assert res.text.count("922222222") == 1
    assert res.text.count("511111111") == 1
    assert res.text.count("911111111") == 1
    assert res.text.count("911111112") == 1
    assert res.text.count("911111113") == 1


def test_research_bar_with_letters_in_meeting_list_in_admin_page(
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_admin,
):
    """Test admin page list all meetings."""
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


def test_research_bar_with_visio_code_in_meeting_list_in_admin_page(
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_admin,
):
    """Test research bar in meeting list with '511111111'."""
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "511111111"
    res = form.submit()
    # Scope the assertions to the meetings table: the search term also appears
    # in the search input and in the language selector links (which preserve the
    # query string), which would otherwise inflate the count.
    meetings_table = res.pyquery("table#meetings").text()
    assert meetings_table.count("922222222") == 0
    assert meetings_table.count("511111111") == 1
    assert meetings_table.count("911111111") == 0
    assert meetings_table.count("911111112") == 0
    assert meetings_table.count("911111113") == 0


def test_research_bar_with_no_result_in_meeting_list_in_admin_page(
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_admin,
):
    """Test research bar in meeting list with 'zzzzzzzzzzzzzzzzz'."""
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


def test_admin_can_edit_meeting_for_other_user(
    user,
    user_2,
    meeting_1_user_2,
    client_app,
    authenticated_admin,
    mock_meeting_is_not_running,
):
    """Test admin can edit meeting owned by an other user."""
    res = client_app.get(f"/meeting/edit/{meeting_1_user_2.id}?", status=200)
    assert res.template == "meeting/wizard.html"
    res.forms[0]["logoutUrl"] = ""
    res = res.forms[0].submit()
    assert (
        "success",
        "delegated meeting modifications prises en compte",
    ) in res.flashes
    assert res.location == f"/admin/meeting/{meeting_1_user_2.id}"


def test_admin_can_create_group(
    user,
    client_app,
    authenticated_admin,
):
    """Test admin can create group."""
    res = client_app.get("/admin/create-group", status=200)
    res.form["name"] = "Group 1"
    res.form["enable_sip"] = None
    res.form["enable_file_sharing"] = None
    res.form["enable_ai_summary"] = None
    res = res.form.submit()
    assert (
        "success",
        "Group 1 a bien été créé(e)",
    ) in res.flashes


def test_create_group_have_a_condition_on_sip(
    user,
    client_app,
    authenticated_admin,
):
    """Test creation group have a condition on enable sip parameter."""
    client_app.app.config["FQDN_SIP_SERVER"] = None
    res = client_app.get("/admin/create-group", status=200)
    assert "disabled" in res.form["enable_sip"].attrs


def test_admin_cannot_create_group_with_existing_name(
    user, client_app, authenticated_admin, group
):
    """Test group name is a unique value."""
    res = client_app.get("/admin/create-group", status=200)
    res.form["name"] = "Group 1"
    res.form["enable_sip"] = None
    res.form["enable_file_sharing"] = None
    res.form["enable_ai_summary"] = None
    res = res.form.submit()
    assert "Ce nom est déjà utilisé." in res.text
    assert db.session.scalar(db.select(db.func.count()).select_from(Group)) == 1


def test_admin_can_display_groups(user, client_app, authenticated_admin, group):
    """Test admin can display groups."""
    res = client_app.get("/admin/groups", status=200)
    assert "Group 1" in res.text


def test_admin_can_add_member_in_group(
    user, client_app, authenticated_admin, group, caplog
):
    """Test admin can add a user in a group."""
    res = client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    assert len(group.members) == 1
    assert ("success", "1 membre ajouté au groupe") in res.flashes
    assert "alice@domain.tld became member of group 1 Group 1" in caplog.text
    assert "1 membre" in res.follow().text


def test_admin_cannot_add_member_already_in_group(
    user, client_app, authenticated_admin, group
):
    """Test adding an already-member user again does not duplicate them."""
    client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    res = client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    category, message = res.flashes[0]
    assert category == "success"
    assert message.startswith("0 membre")
    assert len(group.members) == 1
    assert "1 membre" in res.follow().text


def test_admin_can_remove_member_from_group(
    user, client_app, authenticated_admin, group, caplog
):
    """Test admin can remove member from group."""
    res = client_app.post("/admin/add-group-members/1", {"user_ids": [1]}, status=302)
    res = client_app.get("/admin/manage-group-members/1")
    res = form_with_action(res, "/admin/manage-group-members/1/1").submit(status=302)
    assert ("success", "L'utilisateur a été retiré du groupe") in res.flashes
    assert "alice@domain.tld member removed from group 1 Group 1" in caplog.text


def test_admin_can_read_information_removing_non_member_user(
    user, user_2, client_app, authenticated_admin, group
):
    """Test admin can read inforamtion removing non member user."""
    res = client_app.get("/admin/manage-group-members/1", status=200)
    res.form["search"] = "alice@domain.tld"
    res = res.form.submit()
    res = client_app.post("/admin/manage-group-members/1/2", status=302)
    assert ("error", "L'utilisateur ne fait pas partie du groupe") in res.flashes


def test_admin_can_read_group_infos_before_confirm_group_removing(
    user, client_app, authenticated_admin, group
):
    """Test admin can read group infos before confirm group removing."""
    res = client_app.get("/admin/delete-group/1", status=200)
    assert res.template == "admin/delete_group.html"


def test_research_bar_with_no_result_in_group_list_in_admin_page(
    user, client_app, authenticated_admin, group
):
    """Test search with no result in groups."""
    res = client_app.get("/admin/groups", status=200)
    res.form["search"] = "zzz"
    res = res.form.submit()
    assert "Aucun groupe ne correspond à cette recherche." in res.text


def test_research_bar_with_digit_in_group_list_in_admin_page(
    user, client_app, authenticated_admin, group
):
    """Test search with digit in groups."""
    res = client_app.get("/admin/groups", status=200)
    res.form["search"] = "1"
    res = res.form.submit()
    assert "Group 1" in res.text


def test_research_bar_with_letters_in_group_list_in_admin_page(
    user, client_app, authenticated_admin, group
):
    """Test search with letters in groups."""
    res = client_app.get("/admin/groups", status=200)
    res.form["search"] = "gro"
    res = res.form.submit()
    assert "Group 1" in res.text


def test_research_bar_is_kept_through_pagination_in_group_list_in_admin_page(
    user, client_app, authenticated_admin, mocker
):
    """The group search criteria must survive when navigating to another page."""
    # 'team' matches Team-x (page 1) and Team-y (page 2) but not Squad, so
    # without the filter page 2 would show Squad instead of Team-y.
    for i, name in enumerate(["Team-x", "Squad", "Team-y"]):
        db.session.add(Group(name=name, created_at=datetime(2024, 1, 1 + i)))
    db.session.commit()
    mocker.patch("b3desk.endpoints.admin.PER_PAGE", 1)
    res = client_app.get("/admin/groups?search=team&page=2", status=200)
    groups_table = res.pyquery("table#groups").text()
    assert "Team-y" in groups_table
    assert "Team-x" not in groups_table
    assert "Squad" not in groups_table


def test_admin_can_remove_group(user, client_app, authenticated_admin, group, caplog):
    """Test admin can remove group."""
    res = client_app.get("/admin/delete-group/1")
    res = form_with_action(res, "/admin/confirm-delete-group/1").submit(status=302)
    assert ("success", "Le groupe a été supprimé") in res.flashes
    assert "Groupe 1 Group 1 deleted" in caplog.text
    groups = db.session.scalars(db.select(Group)).all()
    assert len(groups) == 0


def test_admin_can_edit_group(user, client_app, authenticated_admin, group, caplog):
    """Test admin can edit group."""
    res = client_app.get("/admin/edit-group/1", status=200)
    res.form["name"] = "Group 2"
    res.form["enable_sip"] = None
    res.form["enable_file_sharing"] = None
    res.form["enable_ai_summary"] = None
    res.form.submit()
    assert (
        "Group Group 2 1 was updated by admin@domain.tld. Updated fields : {'name': 'Group 2', 'enable_sip': None, 'enable_file_sharing': None, 'enable_ai_summary': None}"
        in caplog.text
    )
    group = db.session.get(Group, 1)
    assert group.name == "Group 2"


def test_edit_group_invalid_form(client_app, authenticated_admin, group):
    """Test group edition form dipsplay message if not validated."""
    res = client_app.get(f"/admin/edit-group/{group.id}", status=200)
    res.form["name"] = ""
    res = res.form.submit()
    assert res.status_int == 200
    assert ("error", "Le formulaire contient des erreurs") in res.flashes


def test_admin_can_toggledownload_meeting_file_not_owner_meeting(
    client_app, authenticated_admin, meeting
):
    """Test admin can toggle download meeting file."""
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


def test_admin_can_delete_meeting_file(client_app, authenticated_admin, meeting):
    """Test admin can delete meeting file."""
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
    assert db.session.scalar(db.select(db.func.count()).select_from(MeetingFiles)) == 0


def test_admin_can_update_recording_name(
    client_app, authenticated_admin, bbb_getRecordings_response
):
    """Test admin can update recording name."""
    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    recording_id = other_meeting.bbb.get_recordings()[0]["recordID"]

    response = client_app.post(
        f"/meeting/{other_meeting.id}/recordings/{recording_id}",
        {"name": "First recording"},
        status=302,
    )

    bbb_url = str(bbb_getRecordings_response.calls.last.request.url)
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/updateRecordings"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params["meta_name"] == "First recording"
    assert bbb_params["recordID"] == recording_id

    assert f"meeting/recordings/{other_meeting.id}" in response.location


###


def test_admin_can_delete_recordings(
    mocker,
    client_app,
    authenticated_admin,
    bbb_getRecordings_response,
    caplog,
):
    """Test admin can delete recordings."""
    from b3desk.models.bbb import BBB

    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("httpx2.Client.get", return_value=DirectLinkRecording)
    recordings = BBB(other_meeting.bbb_meeting_id).get_recordings()

    assert len(recordings) == 2
    first_recording_id = recordings[0]["recordID"]

    response = client_app.post(
        f"/meeting/{other_meeting.id}/video/delete",
        {"recordID": first_recording_id},
    )

    assert (
        f"Meeting Other meeting {other_meeting.id} record {first_recording_id} was deleted by admin@domain.tld\n"
    ) in caplog.text
    assert ("success", "Vidéo supprimée") in response.flashes


def test_admin_can_open_recordings_page(
    client_app,
    authenticated_admin,
    mocker,
    bbb_response,
    bbb_getRecordings_response,
):
    """Test admin can open recordings page."""
    from b3desk.models.bbb import BBB

    other_user = User(email="other@example.com")
    db.session.add(other_user)
    db.session.flush()

    other_meeting = Meeting(name="Other meeting", owner=other_user)
    db.session.add(other_meeting)
    assign_unique_codes(other_meeting)
    db.session.commit()

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("httpx2.Client.get", return_value=DirectLinkRecording)
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)

    response = client_app.get(f"/meeting/recordings/{other_meeting.id}")
    html = response.body.decode("utf-8")
    assert (
        html.count(
            '<button type="button" class="btn-copy fr-btn fr-btn--primary fr-ml-1v fr-icon-clipboard-line copy-button"'
        )
        == 2
    )
    assert len(BBB(other_meeting.bbb_meeting_id).get_recordings()) == 2


def test_admin_can_read_meeting_infos(
    user, meeting_2_user_2, client_app, authenticated_admin
):
    """Test admin can read meeting infos."""
    res = client_app.get(f"/admin/meeting/{meeting_2_user_2.id}", status=200)
    assert res.text.count("922222221") == 5
    assert res.text.count("222222221") == 3
    assert res.text.count("Berenice Cooler") == 1


def test_admin_cannot_edit_files_if_meeting_owner_cannot_use_file_sharing(
    client_app, authenticated_admin, user_2, meeting_2_user_2, group_2
):
    """Test admin cannot edit meeting files if owner cannot use file sharing."""
    res = client_app.post(
        f"/admin/add-group-members/{group_2.id}", {"user_ids": [user_2.id]}, status=302
    )
    assert user_2.groups[0].name == "Group 2"
    res = client_app.get(
        url_for("meeting_files.edit_meeting_files", meeting=meeting_2_user_2),
        status=302,
    )
    assert ("warning", "Vous ne pouvez pas modifier cet élément") in res.flashes


def test_admin_cannot_enter_admin_page_with_admin_management_disabled(
    client_app, authenticated_admin
):
    """Test admin cannot enter admin page when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    client_app.get("/admin/home", status=403)


def test_admin_cannot_edit_meeting_for_other_user_with_admin_management_disabled(
    user_2, meeting_2_user_2, client_app, authenticated_admin
):
    """Test admin is sent to the user login page when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    res = client_app.get(f"/meeting/edit/{meeting_2_user_2.id}", status=302)
    assert res.location.startswith(url_for("public.login"))


def test_admin_cannot_delete_meeting_for_other_user_with_admin_management_disabled(
    user_2, meeting_2_user_2, client_app, authenticated_admin
):
    """Test admin cannot delete other user meeting when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    res = client_app.post(f"/meeting/{meeting_2_user_2.id}/delete", status=302)
    assert res.location.startswith(url_for("public.login"))
    assert db.session.get(Meeting, meeting_2_user_2.id)


def test_admin_cannot_delete_meeting_file_with_admin_management_disabled(
    client_app, authenticated_admin
):
    """Test admin cannot delete other user meeting file when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
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

    client_app.post(
        url_for("meeting_files.delete_meeting_file"),
        params=json.dumps({"id": meeting_file.id}),
        headers={"Content-Type": "application/json"},
        status=403,
    )
    assert db.session.scalar(db.select(db.func.count()).select_from(MeetingFiles)) == 1


def test_admin_cannot_transfer_meeting_ownership_with_admin_management_disabled(
    user_2, meeting_2_user_2, client_app, authenticated_admin
):
    """Test admin cannot transfer other user meeting when admin management is disabled."""
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    client_app.post(
        f"/meeting/transfert-meeting-ownership/{meeting_2_user_2.id}/{user_2.id}",
        status=302,
    )
    assert meeting_2_user_2.owner is user_2


def test_admin_cannot_add_favorite(
    client_app,
    authenticated_admin,
    user,
    meeting,
    bbb_response,
):
    """Test that admin cannot add favorite."""
    response = client_app.post(
        f"/meeting/{meeting.id}/favorite?order_key=created_at&reverse_order=true&favorite_filter=true"
    )
    assert ("error", "L'administrateur n'a pas de favori") in response.flashes
    assert response.location == f"/admin/meeting/{meeting.id}"


def test_admin_login_route_send_404_when_admin_disabled(
    client_app,
):
    client_app.app.config["OIDC_ADMIN_ENABLED"] = False
    response = client_app.get("/admin/login", status=404)
    print(response)
    assert "Cette page n'existe pas." in response
