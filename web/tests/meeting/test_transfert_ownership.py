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
    res = client_app.get("/meeting/transfert-meeting-ownership/1", status=200)
    form = res.form
    form["select"] = 2
    form.submit()
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


def test_transfert_form_display_message_if_empty_form(
    client_app, authenticated_user, meeting
):
    """Test form displays message if form is empty."""
    res = client_app.get("/meeting/transfert-meeting-ownership/1", status=200)
    form = res.form
    form["select"] = ""
    res = form.submit()
    assert ("error", "Vous devez sélectionner un délégataire") in res.flashes
