from b3desk.models.intermediate_tables import Permission


def create_delegate_permission_for_user(user_id, meeting_id):
    permission = Permission(
        user_id=user_id,
        meeting_id=meeting_id,
        permission=1,
    )
    permission.save()
    return


def test_delegated_meetings_visibility_on_welcome_page(
    client_app,
    authenticated_user,
    user,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    bbb_response,
):
    """Test that the delegated meeting appears in meeting list."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    response = client_app.get("/welcome", status=200)
    response.mustcontain("delegated meeting")
    html = response.body.decode("utf-8")
    assert (
        html.count('class="fr-btn fr-btn--secondary fr-icon-user-setting-line"') == 3
    )  # nom de boutons "gérer les délégations"
    assert (
        html.count('class="fr-btn fr-btn--secondary fr-fi-delete-line"') == 3
    )  # nombre de boutons "supprimer"
    assert (
        html.count('class="fr-btn fr-btn--secondary fr-icon-edit-line"') == 4
    )  # nombre de boutons "modifier"
    assert html.count('class="fr-icon-team-line"') == 1  # nombre d'icône "délégataire"


def test_add_and_remove_favorite_delegated_meeting(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegated meetings can be added and removed from favorites."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    assert authenticated_user not in meeting_1_user_2.favorite_of
    response = client_app.get("/welcome")
    response.mustcontain("delegated meeting")
    assert response.context["meetings"] == [
        meeting_1_user_2,
        meeting_3,
        meeting_2,
        meeting,
    ]
    response = client_app.post(
        "/meeting/favorite?order-key=created_at&reverse-order=true&favorite-filter=true",
        {"id": meeting_1_user_2.id},
    ).follow()
    print(response.context["meetings"])
    assert response.context["meetings"] == [meeting_1_user_2, meeting_2, meeting]
    assert authenticated_user in meeting_1_user_2.favorite_of

    response = client_app.post(
        "/meeting/favorite?order-key=created_at&reverse-order=true&favorite-filter=true",
        {"id": meeting_1_user_2.id},
    ).follow()
    assert response.context["meetings"] == [meeting_2, meeting]
    assert authenticated_user not in meeting_1_user_2.favorite_of


def test_delegate_can_launch_delegated_meeting(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegate can launch delegated meeting as owner."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    response = client_app.get(
        f"/meeting/join/{meeting_1_user_2.id}/moderateur", status=302
    )
    assert (
        "https://bbb.test/join?fullName=Alice+Cooper&meetingID=meeting-persistent-1"
        in response.location
    )


def test_delegate_can_see_records_of_delegated_meeting(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegate can see and manage records of a delegated meeting as owner."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    client_app.get("/meeting/recordings/1", status=200)


def test_delegate_can_edit_delegated_meeting(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that meeting edit form displays as owner."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    response = client_app.get(f"/meeting/edit/{meeting_1_user_2.id}", status=200)
    assert response.template == "meeting/wizard.html"


def test_delegate_can_see_delegated_meeting_files(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that meeting see delegated meeting files as owner."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    response = client_app.get(f"/meeting/files/{meeting_1_user_2.id}", status=200)
    assert response.template == "meeting/filesform.html"


def test_delegate_cannot_delete_meeting(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegate cannot delete a delegated meeting."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    response = client_app.post("/meeting/delete", {"id": meeting_1_user_2.id})
    assert ("error", "Vous ne pouvez pas supprimer cet élément") in response.flashes


def test_owner_can_add_new_delegate(
    client_app,
    authenticated_user,
    user_2,
    meeting,
    bbb_response,
    caplog,
):
    """Test that delegate can add a new delegate."""
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert (
        "success",
        "L'utilisateur a été ajouté aux délégataires",
    ) in response.flashes
    assert user_2 in meeting.get_all_delegates
    assert (
        f"{user_2.email} became delegate of meeting {meeting.id} {meeting.name}"
        in caplog.text
    )


def test_add_new_delegate_with_wrong_email(
    client_app,
    authenticated_user,
    meeting,
    bbb_response,
):
    """Test there is a flash message when adding a wrong email."""
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "wrong@domain.tld"
    response = form.submit()
    assert ("error", "L'utilisateur recherché n'existe pas") in response.flashes
    assert meeting.get_all_delegates == []


def test_maximum_delegate_number_limit(
    client_app,
    authenticated_user,
    meeting,
    bbb_response,
    user_2,
    user_3,
):
    """Test that owner cannot add a new delegate beyong the MAXIMUM_MEETING_DELEGATES."""
    client_app.app.config["MAXIMUM_MEETING_DELEGATES"] = 1
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert (
        "success",
        "L'utilisateur a été ajouté aux délégataires",
    ) in response.flashes
    assert user_2 in meeting.get_all_delegates
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "charlie@domain.tld"
    response = form.submit()
    assert (
        "warning",
        "ce séminaire ne peut plus recevoir de nouvelle délégation",
    ) in response.flashes
    assert user_3 not in meeting.get_all_delegates


def test_owner_cannot_add_himself_as_delegate(
    client_app,
    authenticated_user,
    user,
    meeting,
    bbb_response,
):
    """Test that owner cannot add himself as delegate."""
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "alice@domain.tld"
    response = form.submit()
    assert ("error", "L'utilisateur recherché n'existe pas") in response.flashes
    assert meeting.get_all_delegates == []


def test_add_delegate_who_is_already_delegate(
    client_app,
    authenticated_user,
    user,
    meeting,
    bbb_response,
    user_2,
):
    """Test that there is a flash message when adding a delegate aready delegate."""
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert (
        "success",
        "L'utilisateur a été ajouté aux délégataires",
    ) in response.flashes
    assert user_2 in meeting.get_all_delegates

    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert ("warning", "L'utilisateur est déjà délégataire") in response.flashes
    assert len(meeting.get_all_delegates) == 1


def test_owner_can_remove_delegation(
    client_app,
    authenticated_user,
    user,
    meeting,
    bbb_response,
    user_2,
    caplog,
):
    """Test that owner can remove delegation."""
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert (
        "success",
        "L'utilisateur a été ajouté aux délégataires",
    ) in response.flashes
    assert user_2 in meeting.get_all_delegates
    response = client_app.get("/meeting/remove-delegation/1/2", status=302)
    assert (
        "success",
        "L'utilisateur a été retiré des délégataires",
    ) in response.flashes
    assert meeting.get_all_delegates == []
    assert (
        f"{user_2.email} removed from delegates of meeting {meeting.id} {meeting.name}"
        in caplog.text
    )


def test_flash_message_when_delete_wrong_delegation(
    client_app,
    authenticated_user,
    user,
    meeting,
    bbb_response,
    user_2,
):
    """Test there is a flash message when owner delete a wrong delegation."""
    response = client_app.get("/meeting/remove-delegation/1/2")
    assert (
        "error",
        "L'utilisateur ne fait pas partie des délégataires",
    ) in response.flashes


def test_delegate_cannot_remove_delegation(
    client_app, authenticated_user, user, meeting_1_user_2, bbb_response, user_2
):
    """Test that delegate cannot remove delegation."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    client_app.get("/meeting/remove-delegation/1/1", status=403)
    assert user in meeting_1_user_2.get_all_delegates


def test_delegate_cannot_access_delegation_page(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegate cannot access to the delegation page of a delegated meeting."""
    create_delegate_permission_for_user(authenticated_user.id, meeting_1_user_2.id)
    client_app.get("/meeting/manage-delegation/1", status=403)
