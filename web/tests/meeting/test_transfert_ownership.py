from b3desk.models import db
from b3desk.models.meetings import AccessLevel
from b3desk.models.meetings import MeetingAccess


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
    client_app.get("/meeting/transfert-meeting-ownership/1/2", status=302)
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
    client_app.get("/meeting/transfert-meeting-ownership/1/2", status=404)
