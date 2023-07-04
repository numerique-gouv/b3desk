from datetime import datetime, timezone

import pytest

from flaskr.models import Meeting


@pytest.fixture()
def bbb_getRecordings_response(mocker):
    class Resp:
        """Example response inspired from https://docs.bigbluebutton.org/dev/api.html#getrecordings"""

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

    mocker.patch("requests.get", return_value=Resp)


def test_get_recordings(app, meeting, bbb_getRecordings_response):
    with app.app_context():
        meeting = Meeting.query.get(1)
        recordings = meeting.bbb.get_recordings()

    assert len(recordings) == 2
    first_recording = recordings[0]
    assert first_recording["participants"] == 3
    playbacks = first_recording["playbacks"]
    assert len(playbacks) == 2
    assert (
        playbacks["presentation"]["url"]
        == "https://demo.bigbluebutton.org/playback/presentation/2.0/playback.html?meetingId=ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124"
    )
    assert (
        playbacks["video"]["url"]
        == "https://demo.bigbluebutton.org/podcast/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/meeting.mp4"
    )

    assert playbacks["video"]["images"] == []
    images = playbacks["presentation"]["images"]
    assert len(images) == 3
    assert (
        images[0]["url"]
        == "https://demo.bigbluebutton.org/presentation/ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124/presentation/d2d9a672040fbde2a47a10bf6c37b6a4b5ae187f-1530718721134/thumbnails/thumb-1.png"
    )
    assert first_recording["start_date"] == datetime(
        2018, 7, 4, 15, 38, 41, tzinfo=timezone.utc
    )
    second_recording = recordings[1]
    assert second_recording["recordID"] != first_recording["recordID"]
    assert (
        second_recording["recordID"].split("-")[0]
        == first_recording["recordID"].split("-")[0]
    )


def test_update_recording_name(client_app, app, authenticated_user, meeting, mocker):
    class Resp:
        content = """<response><returncode>SUCCESS</returncode><updated>true</updated></response>"""

    mocked_bbb_request = mocker.patch("requests.get", return_value=Resp)

    with app.app_context():
        meeting = Meeting.query.get(1)
        meeting_id = meeting.id

    response = client_app.post(
        f"meeting/{meeting_id}/recordings/recording_id",
        data={"name": "First recording"},
    )

    bbb_url = mocked_bbb_request.call_args.args
    assert f"{app.config['BIGBLUEBUTTON_ENDPOINT']}/updateRecordings" in bbb_url
    bbb_params = mocked_bbb_request.call_args.kwargs["params"].items()
    assert ("meta_name", "First recording") in bbb_params
    assert ("recordID", "recording_id") in bbb_params

    assert response.status_code == 302
    assert f"meeting/recordings/{meeting_id}" in response.location
