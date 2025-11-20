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
    client_app.get("/meeting/recordings/1", status=200)


def test_delegate_can_edit_delegated_meeting(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that meeting edit form displays as owner."""
    response = client_app.get(f"/meeting/edit/{meeting_1_user_2.id}", status=200)
    assert response.template == "meeting/wizard.html"


def test_delegate_can_see_delegated_meeting_files(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that meeting see delegated meeting files as owner."""
    response = client_app.get(f"/meeting/files/{meeting_1_user_2.id}", status=200)
    assert response.template == "meeting/filesform.html"
