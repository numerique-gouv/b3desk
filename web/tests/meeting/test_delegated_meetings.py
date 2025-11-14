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
