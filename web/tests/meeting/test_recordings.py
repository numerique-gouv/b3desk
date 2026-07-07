import datetime
from datetime import timezone
from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
from b3desk.commands import bp


@pytest.fixture
def bbb_getRecordings_response(mocker):
    """Fixture that provides a mock BBB getRecordings API response with sample recording data."""

    class Response:
        """https://docs.bigbluebutton.org/dev/api.html#getrecordings."""

        content = """
<response>
  <returncode>SUCCESS</returncode>
  <recordings>
    <recording>
      <recordID>ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124</recordID>
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
        <analytics-callback-url>https://bbb-analytics.test</analytics-callback-url>
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
          <url>https://bbb.test/playback/presentation/2.0/playback.html?meetingId=ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124</url>
          <processingTime>7177</processingTime>
          <length>0</length>
          <size>1104836</size>
          <preview>
            <images>
              <image alt="Welcome to" height="136" width="176">https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-1.png</image>
              <image alt="(this slide left blank for use as a whiteboard)" height="136" width="176">https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-2.png</image>
              <image alt="(this slide left blank for use as a whiteboard)" height="136" width="176">https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-3.png</image>
            </images>
          </preview>
        </format>
        <format>
          <type>video</type>
          <url>https://bbb.test/podcast/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/meeting.mp4</url>
          <processingTime>0</processingTime>
          <length>0</length>
          <size>1104836</size>
        </format>
        <format>
          <type>ai-summary</type>
          <url>https://bbb.test/playback/ai-summary/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/ai-summary.html</url>
          <processingTime>0</processingTime>
          <length>0</length>
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
        <analytics-callback-url>https://bbb-analytics.test</analytics-callback-url>
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
          <url>https://bbb.test/podcast/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/audio.ogg</url>
          <processingTime>0</processingTime>
          <length>33</length>
        </format>
        <format>
          <type>presentation</type>
          <url>https://bbb.test/playback/presentation/2.0/playback.html?meetingId=ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111</url>
          <processingTime>139458</processingTime>
          <length>33</length>
          <preview>
            <images>
              <image width="176" height="136" alt="Welcome to">https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530278898120/thumbnails/thumb-1.png</image>
              <image width="176" height="136" alt="(this slide left blank for use as a whiteboard)">https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530278898120/thumbnails/thumb-2.png</image>
              <image width="176" height="136" alt="(this slide left blank for use as a whiteboard)">https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530278898120/thumbnails/thumb-3.png</image>
            </images>
          </preview>
        </format>
        <format>
          <type>ai-summary</type>
          <url>https://bbb.test/playback/ai-summary/ffbfc4cc24428694e8b53a4e144f414052431693-1530278898111/ai-summary.html</url>
          <processingTime>0</processingTime>
          <length>0</length>
        </format>
      </playback>
    </recording>
  </recordings>
</response>
"""
        text = ""

    yield mocker.patch("requests.Session.send", return_value=Response)


@pytest.fixture
def bbb_getRecordings_missing_recordID(mocker):
    """Fixture with missing recordID to trigger AttributeError."""

    class Response:
        content = """
<response>
  <returncode>SUCCESS</returncode>
  <recordings>
    <recording>
      <meetingID>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingID>
      <startTime>1530718721124</startTime>
      <endTime>1530718810456</endTime>
      <participants>3</participants>
      <metadata>
        <name>Fred's Room</name>
      </metadata>
      <playback>
        <format>
          <type>presentation</type>
          <url>https://bbb.test/playback/presentation/2.0/playback.html</url>
        </format>
      </playback>
    </recording>
  </recordings>
</response>
"""
        text = ""

    yield mocker.patch("requests.Session.send", return_value=Response)


@pytest.fixture
def bbb_getRecordings_ai_summary(mocker):
    """Fixture providing a getRecordings response that includes an ai-summary format."""

    class Response:
        content = """
<response>
  <returncode>SUCCESS</returncode>
  <recordings>
    <recording>
      <recordID>rec-ai-1</recordID>
      <meetingID>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingID>
      <internalMeetingID>rec-ai-1</internalMeetingID>
      <name>Meeting with summary</name>
      <startTime>1530718721124</startTime>
      <endTime>1530718810456</endTime>
      <participants>2</participants>
      <metadata>
        <name>Meeting with summary</name>
      </metadata>
      <playback>
        <format>
          <type>presentation</type>
          <url>https://bbb.test/playback/presentation/2.3/rec-ai-1</url>
          <length>0</length>
        </format>
        <format>
          <type>ai-summary</type>
          <url>https://bbb.test/ai-summary/rec-ai-1/ai-summary.html</url>
          <length>0</length>
          <size>38610</size>
          <urls>
            <url type="html">https://bbb.test/ai-summary/rec-ai-1/ai-summary.html</url>
            <url type="json">https://bbb.test/ai-summary/rec-ai-1/transcription.json</url>
          </urls>
        </format>
      </playback>
    </recording>
  </recordings>
</response>
"""
        text = ""

    yield mocker.patch("requests.Session.send", return_value=Response)


def test_get_recordings(mocker, meeting, bbb_getRecordings_response):
    """Test that recordings are retrieved and parsed correctly from BBB."""
    from b3desk.models.bbb import BBB

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)
    recordings = BBB(meeting.meetingID).get_recordings()

    assert len(recordings) == 2
    first_recording = recordings[0]
    assert first_recording["participants"] == 3
    playbacks = first_recording["playbacks"]
    print(playbacks)
    assert len(playbacks) == 3
    assert (
        playbacks["presentation"]["url"]
        == "https://bbb.test/playback/presentation/2.0/playback.html?meetingId=ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124"
    )
    assert (
        playbacks["video"]["url"]
        == "https://bbb.test/podcast/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/meeting.mp4"
    )
    assert (
        playbacks["ai-summary"]["url"]
        == "https://bbb.test/playback/ai-summary/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/ai-summary.html"
    )

    assert playbacks["video"]["images"] == []
    images = playbacks["presentation"]["images"]
    assert len(images) == 3
    assert (
        images[0]["url"]
        == "https://bbb.test/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-1.png"
    )
    assert first_recording["start_date"] == datetime.datetime(
        2018, 7, 4, 15, 38, 41, tzinfo=timezone.utc
    )
    second_recording = recordings[1]
    assert second_recording["recordID"] != first_recording["recordID"]
    assert (
        second_recording["recordID"].split("-")[0]
        == first_recording["recordID"].split("-")[0]
    )


def test_get_recordings_with_missing_recordID(
    mocker, meeting, bbb_getRecordings_missing_recordID, caplog
):
    """Test that exception is caught when recordID is missing."""
    from b3desk.models.bbb import BBB

    recordings = BBB(meeting.meetingID).get_recordings()

    assert isinstance(recordings, list)
    assert len(recordings) == 0
    assert "'NoneType' object has no attribute 'text'" in caplog.text


def test_update_recording_name(client_app, authenticated_user, meeting, bbb_response):
    """Test that recording name can be updated via BBB API."""
    response = client_app.post(
        f"/meeting/{meeting.id}/recordings/recording_id",
        {"name": "First recording"},
        status=302,
    )

    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/updateRecordings"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params["meta_name"] == "First recording"
    assert bbb_params["recordID"] == "recording_id"

    assert f"meeting/recordings/{meeting.id}" in response.location


def test_delete_recordings(
    mocker, client_app, authenticated_user, meeting, bbb_getRecordings_response, caplog
):
    from b3desk.models.bbb import BBB

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)
    recordings = BBB(meeting.meetingID).get_recordings()

    assert len(recordings) == 2
    first_recording_id = recordings[0]["recordID"]

    response = client_app.post(
        f"/meeting/{meeting.id}/video/delete",
        {"recordID": first_recording_id},
    )

    assert (
        f"Meeting meeting {meeting.id} record {first_recording_id} was deleted by alice@domain.tld\n"
    ) in caplog.text
    assert ("success", "Vidéo supprimée") in response.flashes


def test_delegate_can_delete_recordings(
    mocker,
    client_app,
    authenticated_user,
    meeting_1_user_2,
    bbb_getRecordings_response,
    caplog,
):
    """Test delegate can delete a recording."""

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)
    recordings = meeting_1_user_2.bbb.get_recordings()

    assert len(recordings) == 2
    first_recording_id = recordings[0]["recordID"]

    response = client_app.post(
        f"/meeting/{meeting_1_user_2.id}/video/delete",
        {"recordID": first_recording_id},
    )

    assert (
        f"Meeting delegated meeting {meeting_1_user_2.id} record {first_recording_id} was deleted by alice@domain.tld\n"
    ) in caplog.text
    assert ("success", "Vidéo supprimée") in response.flashes


def test_open_recordings_page(
    client_app,
    authenticated_user,
    mocker,
    meeting,
    bbb_response,
    bbb_getRecordings_response,
):
    """Test that recordings are retrieved and parsed correctly from BBB."""
    from b3desk.models.bbb import BBB

    class DirectLinkRecording:
        status_code = 200

    mocker.patch("b3desk.models.bbb.requests.get", return_value=DirectLinkRecording)
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)

    response = client_app.get(f"/meeting/recordings/{meeting.id}")
    html = response.body.decode("utf-8")
    assert (
        html.count(
            '<button type="button" class="btn-copy fr-btn fr-btn--primary fr-ml-1v fr-icon-clipboard-line"'
        )
        == 2
    )
    assert len(BBB(meeting.meetingID).get_recordings()) == 2


def test_derive_ai_summary_playback():
    """PDF and Markdown report URLs are derived from the HTML report URL."""
    from b3desk.models.bbb import derive_ai_summary_playback

    base = "https://bbb.test/ai-summary/rec/ai-summary"
    assert derive_ai_summary_playback(f"{base}.html") == {
        "url": f"{base}.html",
        "pdf": f"{base}.pdf",
        "md": f"{base}.md",
    }

    # A URL that is not an HTML report yields no derivation.
    folder_url = "https://bbb.test/ai-summary/rec/"
    assert derive_ai_summary_playback(folder_url) == {"url": folder_url}


def test_get_recordings_ai_summary(mocker, meeting, bbb_getRecordings_ai_summary):
    """ai-summary playback exposes the HTML report and the derived PDF/Markdown URLs."""
    from b3desk.models.bbb import BBB

    recordings = BBB(meeting.meetingID).get_recordings()

    assert len(recordings) == 1
    summary = recordings[0]["playbacks"]["ai-summary"]
    assert summary == {
        "url": "https://bbb.test/ai-summary/rec-ai-1/ai-summary.html",
        "pdf": "https://bbb.test/ai-summary/rec-ai-1/ai-summary.pdf",
        "md": "https://bbb.test/ai-summary/rec-ai-1/ai-summary.md",
    }


def test_build_recording_links_ai_summary():
    """The notification mail links include the three ai-summary report formats."""
    from b3desk.utils import _build_recording_links

    playbacks = {
        "ai-summary": {
            "url": "https://bbb.test/ai-summary/rec/ai-summary.html",
            "pdf": "https://bbb.test/ai-summary/rec/ai-summary.pdf",
            "md": "https://bbb.test/ai-summary/rec/ai-summary.md",
        }
    }
    links = _build_recording_links(playbacks)

    assert [link["url"] for link in links] == [
        "https://bbb.test/ai-summary/rec/ai-summary.html",
        "https://bbb.test/ai-summary/rec/ai-summary.pdf",
        "https://bbb.test/ai-summary/rec/ai-summary.md",
    ]


def test_open_recordings_page_ai_summary(
    cli_runner,
    client_app,
    authenticated_user,
    mocker,
    meeting,
    bbb_response,
    bbb_getRecordings_ai_summary,
    group,
):
    """The recordings page shows the ai-summary report links (HTML/PDF/Markdown)."""
    mocker.patch("b3desk.models.bbb.BBB.is_running", return_value=False)
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    response = client_app.get("/admin/add-group-members/1/1", status=200)
    response = client_app.get(f"/meeting/recordings/{meeting.id}")
    html = response.body.decode("utf-8")

    assert "https://bbb.test/ai-summary/rec-ai-1/ai-summary.html" in html
    assert "https://bbb.test/ai-summary/rec-ai-1/ai-summary.pdf" in html
    assert "https://bbb.test/ai-summary/rec-ai-1/ai-summary.md" in html
