import flaskr.utils


def test_retry_join_meeting():
    SIGNIN_URL = "http://demo.test/meeting/signin/1/creator/1/hash/1432758aec5073701e4f0d65280a7dc7980a393e"
    WAIT_ROOM_URL = "http://demo.test/meeting/wait/1/creator/1/hash/1432758aec5073701e4f0d65280a7dc7980a393e/fullname/BBB%20User/fullname_suffix/XX"

    assert (
        flaskr.utils.retry_join_meeting(WAIT_ROOM_URL, "authenticated", "Alice", "")
        == True
    )
    assert flaskr.utils.retry_join_meeting(SIGNIN_URL, "attendee", "", "") == False
    assert flaskr.utils.retry_join_meeting(SIGNIN_URL, "attendee", "Alice", "") == True
    assert flaskr.utils.retry_join_meeting(SIGNIN_URL, "moderator", "", "") == False
    assert flaskr.utils.retry_join_meeting(SIGNIN_URL, "moderator", "Alice", "") == True
    assert flaskr.utils.retry_join_meeting(SIGNIN_URL, "authenticated", "", "") == False
    assert (
        flaskr.utils.retry_join_meeting(SIGNIN_URL, "authenticated", "Alice", "")
        == False
    )
    assert (
        flaskr.utils.retry_join_meeting(
            SIGNIN_URL, "authenticated", "Alice", "Service A"
        )
        == True
    )
