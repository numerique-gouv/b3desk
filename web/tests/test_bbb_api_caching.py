import pytest


@pytest.fixture
def configuration(configuration):
    configuration["BIGBLUEBUTTON_API_CACHE_DURATION"] = 5
    return configuration


IS_MEETING_RUNNING_SUCCESS_RESPONSE = """
<response>
  <returncode>SUCCESS</returncode>
  <running>true</running>
</response>
"""


def test_is_meeting_running(meeting, mocker):
    """Tests that the requests to the ismeetingrunning endpoint of the BBB API
    are cached."""

    class Response:
        content = IS_MEETING_RUNNING_SUCCESS_RESPONSE
        text = ""

    send = mocker.patch("requests.Session.send", return_value=Response)

    assert send.call_count == 0

    assert meeting.bbb.is_meeting_running()
    assert send.call_count == 1

    assert meeting.bbb.is_meeting_running()
    assert send.call_count == 1


GET_RECORDINGS_RESPONSE = """
<response>
  <returncode>SUCCESS</returncode>
  <recordings>
    <recording>
      <recordID>ffbfc4cc24428694e8b53a4e144f414052œ431693-1530718721124</recordID>
      <meetingID>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingID>
      <internalMeetingID>ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124</internalMeetingID>
      <name>Fred's Room</name>
      <isBreakout>false</isBreakout>
      <published>true</published>
      <state>published</state>
      <startTime>1530718721124</startTime>
      <endTime>1530718810456</endTime>
      <participants>3</participants>
      <rawSize>951067</rawSize>
      <metadata>
        <analytics-callback-url>https://bbb-analytics.url</analytics-callback-url>
        <isBreakout>false</isBreakout>
        <meetingId>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingId>
        <meetingName>Fred's Room</meetingName>
      </metadata>
      <breakout>
        <parentId>unknown</parentId>
        <sequence>0</sequence>
        <freeJoin>false</freeJoin>
      </breakout>
      <size>1104836</size>
      <playback>
        <format>
          <type>presentation</type>
          <url>https://demo.bigbluebutton.org/playback/presentation/2.0/playback.html?meetingId=ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124</url>
          <processingTime>7177</processingTime>
          <length>0</length>
          <size>1104836</size>
          <preview>
            <images>
              <image alt="Welcome to" height="136" width="176">https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-1.png</image>
              <image alt="(this slide left blank for use as a whiteboard)" height="136" width="176">https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-2.png</image>
              <image alt="(this slide left blank for use as a whiteboard)" height="136" width="176">https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-3.png</image>
            </images>
          </preview>
        </format>
        <format>
          <type>video</type>
          <url>https://demo.bigbluebutton.org/podcast/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/meeting.mp4</url>
          <processingTime>0</processingTime>
          <length>0</length>
          <size>1104836</size>
        </format>
      </playback>
    </recording>
    <recording>
      <recordID>ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111</recordID>
      <meetingID>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingID>
      <internalMeetingID>ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111</internalMeetingID>
      <name>Fred's Room</name>
      <isBreakout>false</isBreakout>
      <published>true</published>
      <state>published</state>
      <startTime>1530278898111</startTime>
      <endTime>1530281194326</endTime>
      <participants>7</participants>
      <rawSize>381530</rawSize>
      <metadata>
        <name>Recording title hand written</name>
        <meetingName>Fred's Room</meetingName>
        <meetingId>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingId>
        <analytics-callback-url>https://bbb-analytics.url</analytics-callback-url>
        <isBreakout>false</isBreakout>
      </metadata>
      <breakout>
        <parentId>unknown</parentId>
        <sequence>0</sequence>
        <freeJoin>false</freeJoin>
      </breakout>
      <playback>
        <format>
          <type>podcast</type>
          <url>https://demo.bigbluebutton.org/podcast/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/audio.ogg</url>
          <processingTime>0</processingTime>
          <length>33</length>
        </format>
        <format>
          <type>presentation</type>
          <url>https://demo.bigbluebutton.org/playback/presentation/2.0/playback.html?meetingId=ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111</url>
          <processingTime>139458</processingTime>
          <length>33</length>
          <preview>
            <images>
              <image width="176" height="136" alt="Welcome to">https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530278898120/thumbnails/thumb-1.png</image>
              <image width="176" height="136" alt="(this slide left blank for use as a whiteboard)">https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530278898120/thumbnails/thumb-2.png</image>
              <image width="176" height="136" alt="(this slide left blank for use as a whiteboard)">https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530278898120/thumbnails/thumb-3.png</image>
            </images>
          </preview>
        </format>
      </playback>
    </recording>
  </recordings>
</response>
"""


def test_get_recordings(meeting, mocker):
    """Tests that the requests to the getrecordings endpoint of the BBB API are
    cached."""

    class Response:
        content = GET_RECORDINGS_RESPONSE
        text = ""

    class DirectLinkRecording:
        status_code = 200

    send = mocker.patch("requests.Session.send", return_value=Response)
    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)

    assert send.call_count == 0

    recordings = meeting.bbb.get_recordings()
    assert len(recordings) == 2
    assert send.call_count == 1

    recordings = meeting.bbb.get_recordings()
    assert len(recordings) == 2
    assert send.call_count == 1


CREATE_RESPONSE = """
<response>
  <returncode>SUCCESS</returncode>
  <meetingID>Test</meetingID>
  <internalMeetingID>640ab2bae07bedc4c163f679a746f7ab7fb5d1fa-1531155809613</internalMeetingID>
  <parentMeetingID>bbb-none</parentMeetingID>
  <attendeePW>ap</attendeePW>
  <moderatorPW>mp</moderatorPW>
  <createTime>1531155809613</createTime>
  <voiceBridge>70757</voiceBridge>
  <dialNumber>613-555-1234</dialNumber>
  <createDate>Mon Jul 09 17:03:29 UTC 2018</createDate>
  <hasUserJoined>false</hasUserJoined>
  <duration>0</duration>
  <hasBeenForciblyEnded>false</hasBeenForciblyEnded>
  <messageKey>duplicateWarning</messageKey>
  <message>This conference was already in existence and may currently be in progress.</message>
</response>
"""


def test_create(meeting, mocker):
    """Tests that the requests to the create endpoint of the BBB API are NOT
    cached."""

    class Response:
        content = CREATE_RESPONSE
        text = ""

    send = mocker.patch("requests.Session.send", return_value=Response)
    mocker.patch("requests.post")

    assert send.call_count == 0

    data = meeting.bbb.create()
    assert data["returncode"] == "SUCCESS"
    assert send.call_count == 1

    data = meeting.bbb.create()
    assert data["returncode"] == "SUCCESS"
    assert send.call_count == 2
