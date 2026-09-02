from b3desk.models import db
from b3desk.models.meetings import AccessLevel
from b3desk.models.meetings import MeetingAccess
from b3desk.models.meetings import MeetingSecretKey
from b3desk.models.roles import Role


def test_owner_can_transfer_ownership_to_delegate(
    client_app, authenticated_user, user_2, meeting, user, smtpd, caplog
):
    """Test owner can transfer ownership to delegate."""
    new_access = MeetingAccess(
        meeting_id=meeting.id,
        user_id=user_2.id,
        level=AccessLevel.DELEGATE,
    )
    db.session.add(new_access)
    db.session.commit()
    client_app.post("/meeting/transfert-meeting-ownership/1/2", status=302)
    assert meeting.owner is user_2
    assert user in meeting.get_all_delegates
    assert len(smtpd.messages) == 2
    assert "Meeting 1 meeting have a new owner : 2 Berenice Cooler" in caplog.text
    assert "alice@domain.tld became delegate of meeting 1 meeting" in caplog.text
    assert (
        "berenice@domain.tld removed from delegates of meeting 1 meeting" in caplog.text
    )
    assert "Email sent to alice@domain.tld" in caplog.text
    assert "Email sent to berenice@domain.tld" in caplog.text


def test_new_owner_is_not_delegate_display_404(
    client_app, authenticated_user, meeting, user_2
):
    """Test form displays message if form is empty."""
    client_app.post("/meeting/transfert-meeting-ownership/1/2", status=404)


def test_transfer_ownership_preserves_shared_invitation_links(
    client_app, authenticated_user, user_2, meeting, user
):
    """Transferring ownership must not change the meeting's existing signin secrets."""
    new_access = MeetingAccess(
        meeting_id=meeting.id,
        user_id=user_2.id,
        level=AccessLevel.DELEGATE,
    )
    db.session.add(new_access)
    db.session.commit()

    moderator_secret_key = MeetingSecretKey.query.filter_by(
        meeting_id=meeting.id, role=Role.moderator.name
    ).one()
    attendee_secret_key = MeetingSecretKey.query.filter_by(
        meeting_id=meeting.id, role=Role.attendee.name
    ).one()
    previous_moderator_secret = moderator_secret_key.secret_key
    previous_attendee_secret = attendee_secret_key.secret_key
    previous_moderator_url = meeting.moderator_url
    previous_attendee_url = meeting.attendee_url

    client_app.post("/meeting/transfert-meeting-ownership/1/2", status=302)

    db.session.refresh(moderator_secret_key)
    db.session.refresh(attendee_secret_key)
    assert moderator_secret_key.secret_key == previous_moderator_secret
    assert attendee_secret_key.secret_key == previous_attendee_secret
    assert meeting.moderator_url == previous_moderator_url
    assert meeting.attendee_url == previous_attendee_url

    response = client_app.get(previous_attendee_url, status=200)
    assert response.template == "meeting/join.html"


def test_transfer_ownership_preserves_previous_owners_recordings_access(
    client_app, authenticated_user, user_2, meeting, user, bbb_response
):
    """After a transfer, the previous owner (now a delegate) must keep recordings access."""
    new_access = MeetingAccess(
        meeting_id=meeting.id,
        user_id=user_2.id,
        level=AccessLevel.DELEGATE,
    )
    db.session.add(new_access)
    db.session.commit()

    client_app.post("/meeting/transfert-meeting-ownership/1/2", status=302)

    client_app.get(f"/meeting/recordings/{meeting.id}", status=200)


def test_transfer_ownership_preserves_new_owners_recordings_access(
    client_app, authenticated_user_2, meeting, user, user_2, bbb_response
):
    """After a transfer, the new owner must have recordings access."""
    meeting.owner = user_2
    db.session.add(
        MeetingAccess(
            meeting_id=meeting.id,
            user_id=user.id,
            level=AccessLevel.DELEGATE,
        )
    )
    db.session.commit()

    client_app.get(f"/meeting/recordings/{meeting.id}", status=200)
