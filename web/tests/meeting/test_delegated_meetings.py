import json
from datetime import date

from b3desk.models import db
from b3desk.models.meetings import MeetingFiles
from flask import url_for


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
    )  # nombre de boutons "gérer les délégations"
    assert (
        html.count('class="fr-btn fr-btn--secondary fr-fi-delete-line"') == 3
    )  # nombre de boutons "supprimer"
    assert (
        html.count('class="fr-btn fr-btn--secondary fr-icon-edit-line"') == 4
    )  # nombre de boutons "modifier"
    assert (
        html.count('<i class="fr-icon-parent-fill delegated-icon"') == 1
    )  # nombre d'icône "délégataire"


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
    assert "need-confirm" in str(response.html)
    response.forms[0]["voiceBridge"] = "123456789"
    response = response.forms[0].submit()
    assert "Vous n'êtes pas priopriétaire" in response


def test_delegate_can_see_delegated_meeting_files(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that meeting see delegated meeting files as owner."""
    response = client_app.get(f"/meeting/files/{meeting_1_user_2.id}", status=200)
    assert response.template == "meeting/filesform.html"


def test_delegate_cannot_delete_meeting(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegate cannot delete a delegated meeting."""
    response = client_app.post("/meeting/delete", {"id": meeting_1_user_2.id})
    assert ("error", "Vous ne pouvez pas supprimer cet élément") in response.flashes


def test_owner_can_add_new_delegate(
    client_app,
    authenticated_user,
    user_2,
    meeting,
    bbb_response,
    caplog,
    smtpd,
):
    """Test that delegate can add a new delegate."""
    assert len(smtpd.messages) == 0
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
    assert len(smtpd.messages) == 1


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
    smtpd,
):
    """Test that owner cannot add a new delegate beyong the MAXIMUM_MEETING_DELEGATES."""
    assert len(smtpd.messages) == 0
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
    assert len(smtpd.messages) == 1
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "charlie@domain.tld"
    response = form.submit()
    assert (
        "warning",
        "ce séminaire ne peut plus recevoir de nouvelle délégation",
    ) in response.flashes
    assert user_3 not in meeting.get_all_delegates
    assert len(smtpd.messages) == 1


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
    smtpd,
):
    """Test that there is a flash message when adding a delegate aready delegate."""
    assert len(smtpd.messages) == 0
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert (
        "success",
        "L'utilisateur a été ajouté aux délégataires",
    ) in response.flashes
    assert user_2 in meeting.get_all_delegates
    assert len(smtpd.messages) == 1

    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert ("warning", "L'utilisateur est déjà délégataire") in response.flashes
    assert len(meeting.get_all_delegates) == 1
    assert len(smtpd.messages) == 1


def test_owner_can_remove_delegation(
    client_app,
    authenticated_user,
    user,
    meeting,
    bbb_response,
    user_2,
    caplog,
    smtpd,
):
    """Test that owner can remove delegation."""
    assert len(smtpd.messages) == 0
    response = client_app.get("/meeting/manage-delegation/1", status=200)
    form = response.form
    form["search"] = "berenice@domain.tld"
    response = form.submit()
    assert (
        "success",
        "L'utilisateur a été ajouté aux délégataires",
    ) in response.flashes
    assert user_2 in meeting.get_all_delegates
    assert len(smtpd.messages) == 1
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
    assert len(smtpd.messages) == 2


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
    client_app.get("/meeting/remove-delegation/1/1", status=403)
    assert user in meeting_1_user_2.get_all_delegates


def test_delegate_cannot_access_delegation_page(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test that delegate cannot access to the delegation page of a delegated meeting."""
    client_app.get("/meeting/manage-delegation/1", status=403)


def test_smtp_error_when_sending_delegation_mail(
    client_app,
    authenticated_user,
    user_2,
    meeting,
    bbb_response,
    caplog,
    smtpd,
):
    """Test there is a log when cannot connect to smtp to send delegation mail."""
    client_app.app.config["SMTP_HOST"] = None
    assert len(smtpd.messages) == 0
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
    assert (
        f"Could not connect to SMTP host {client_app.app.config['SMTP_HOST']}"
        in caplog.text
    )

    assert len(smtpd.messages) == 0


def test_delegate_can_delete_meeting_file(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_response,
):
    """Test delegate can delete a meeting file as owner."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting_1_user_2.id,
        owner=meeting_1_user_2.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()
    file_id = meeting_file.id

    response = client_app.post(
        url_for("meeting_files.delete_meeting_file"),
        params=json.dumps({"id": file_id}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_int == 200
    assert response.json["id"] == file_id
    assert "supprimé avec succès" in response.json["msg"]
    assert db.session.get(MeetingFiles, file_id) is None
