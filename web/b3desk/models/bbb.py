# +----------------------------------------------------------------------------+
# | BBB-VISIO                                                                  |
# +----------------------------------------------------------------------------+
#
#   This program is free software: you can redistribute it and/or modify it
# under the terms of the European Union Public License 1.2 version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
import hashlib
from datetime import datetime
from datetime import timezone
from xml.etree import ElementTree

import requests
from flask import current_app
from flask import render_template
from flask import url_for

from b3desk.tasks import background_upload


class BBB:
    """Interface to BBB API."""

    def __init__(self, meeting):
        self.meeting = meeting

    def bbb_request(self, action, method="GET", **kwargs):
        request = requests.Request(
            method=method,
            url="{}/{}".format(current_app.config["BIGBLUEBUTTON_ENDPOINT"], action),
            **kwargs,
        )
        prepped = request.prepare()
        bigbluebutton_secret = current_app.config["BIGBLUEBUTTON_SECRET"]
        secret = "{}{}".format(
            prepped.url.replace("?", "").replace(
                f'{current_app.config["BIGBLUEBUTTON_ENDPOINT"]}/', ""
            ),
            bigbluebutton_secret,
        )
        checksum = hashlib.sha1(secret.encode("utf-8")).hexdigest()
        prepped.prepare_url(prepped.url, params={"checksum": checksum})
        return prepped

    def bbb_response(self, request):
        session = requests.Session()
        current_app.logger.debug("BBB API request %s: %s", request.method, request.url)
        response = session.send(request)
        return {c.tag: c.text for c in ElementTree.fromstring(response.content)}

    def is_meeting_running(self):
        """https://docs.bigbluebutton.org/development/api/#ismeetingrunning"""
        request = self.bbb_request(
            "isMeetingRunning", params={"meetingID": self.meeting.meetingID}
        )
        return self.bbb_response(request)

    def create(self):
        """https://docs.bigbluebutton.org/development/api/#create"""
        params = {
            "meetingID": self.meeting.meetingID,
            "name": self.meeting.name,
            "uploadExternalUrl": url_for(
                "meetings.externalUpload", meeting=self.meeting, _external=True
            ),
            "uploadExternalDescription": current_app.config[
                "EXTERNAL_UPLOAD_DESCRIPTION"
            ],
        }
        if (param := self.meeting.record) is not None:
            params["record"] = str(param).lower()
        if (param := self.meeting.autoStartRecording) is not None:
            params["autoStartRecording"] = str(param).lower()
        if (param := self.meeting.allowStartStopRecording) is not None:
            params["allowStartStopRecording"] = str(param).lower()
        if (param := self.meeting.webcamsOnlyForModerator) is not None:
            params["webcamsOnlyForModerator"] = str(param).lower()
        if (param := self.meeting.muteOnStart) is not None:
            params["muteOnStart"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisableCam) is not None:
            params["lockSettingsDisableCam"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisableMic) is not None:
            params["lockSettingsDisableMic"] = str(param).lower()
        if (param := self.meeting.allowModsToUnmuteUsers) is not None:
            params["allowModsToUnmuteUsers"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisablePrivateChat) is not None:
            params["lockSettingsDisablePrivateChat"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisablePublicChat) is not None:
            params["lockSettingsDisablePublicChat"] = str(param).lower()
        if (param := self.meeting.lockSettingsDisableNote) is not None:
            params["lockSettingsDisableNote"] = str(param).lower()
        if param := self.meeting.attendeePW:
            params["attendeePW"] = param
        if param := self.meeting.moderatorPW:
            params["moderatorPW"] = param
        if param := self.meeting.welcome:
            params["welcome"] = param
        if param := self.meeting.maxParticipants:
            params["maxParticipants"] = str(param)
        if param := self.meeting.logoutUrl:
            params["logoutURL"] = str(param)
        if param := self.meeting.duration:
            params["duration"] = str(param)
        bigbluebutton_analytics_callback_url = current_app.config[
            "BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"
        ]
        if bigbluebutton_analytics_callback_url:
            # bbb will call this endpoint when meeting ends
            params.update(
                {
                    "meetingKeepEvents": "true",
                    "meta_analytics-callback-url": str(
                        bigbluebutton_analytics_callback_url
                    ),
                }
            )
        if self.meeting.attendeePW is None:
            # if no attendeePW it a meeting create with a mail (not logged in)
            params["moderatorOnlyMessage"] = render_template(
                "meeting/signin_mail_link.html",
                main_message=self.meeting.moderatorOnlyMessage,
                link=self.meeting.get_mail_signin_url(),
            )
        else:
            quick_meeting_moderator_link_introduction = current_app.config[
                "QUICK_MEETING_MODERATOR_LINK_INTRODUCTION"
            ]
            quick_meeting_attendee_link_introduction = current_app.config[
                "QUICK_MEETING_ATTENDEE_LINK_INTRODUCTION"
            ]
            params["moderatorOnlyMessage"] = render_template(
                "meeting/signin_links.html",
                moderator_message=self.meeting.moderatorOnlyMessage,
                moderator_link_introduction=quick_meeting_moderator_link_introduction,
                moderator_signin_url=self.meeting.get_signin_url("moderator"),
                attendee_link_introduction=quick_meeting_attendee_link_introduction,
                attendee_signin_url=self.meeting.get_signin_url("attendee"),
            )
        params["guestPolicy"] = (
            "ASK_MODERATOR" if self.meeting.guestPolicy else "ALWAYS_ACCEPT"
        )

        if not current_app.config["FILE_SHARING"]:
            request = self.bbb_request("create", params=params)
            return self.bbb_response(request)

        # default file is sent right away since it is need as the background
        # image for the meeting
        xml = (
            self.meeting_file_addition_xml([self.meeting.default_file])
            if self.meeting.default_file
            else None
        )
        request = self.bbb_request("create", "POST", params=params, data=xml)
        data = self.bbb_response(request)

        # non default files are sent later
        if self.meeting.non_default_files:
            xml = self.meeting_file_addition_xml(self.meeting.non_default_files)
            request = self.bbb_request(
                "insertDocument", params={"meetingID": self.meeting.meetingID}
            )
            background_upload.delay(request.url, xml)

        return data

    def delete_recordings(self, recording_ids):
        """https://docs.bigbluebutton.org/dev/api.html#deleterecordings"""
        request = self.bbb_request(
            "deleteRecordings", params={"recordID": recording_ids}
        )
        return self.bbb_response(request)

    def get_meeting_info(self):
        """https://docs.bigbluebutton.org/development/api/#getmeetinginfo"""
        request = self.bbb_request(
            "getMeetingInfo", params={"meetingID": self.meeting.meetingID}
        )
        return self.bbb_response(request)

    def get_recordings(self):
        """https://docs.bigbluebutton.org/development/api/#getrecordings"""
        request = self.bbb_request(
            "getRecordings", params={"meetingID": self.meeting.meetingID}
        )
        current_app.logger.debug("BBB API request %s: %s", request.method, request.url)
        response = requests.Session().send(request)

        root = ElementTree.fromstring(response.content)
        return_code = root.find("returncode").text
        recordings = root.find("recordings")
        result = []
        if return_code != "FAILED" and recordings:
            try:
                for recording in recordings.iter("recording"):
                    data = {}
                    data["recordID"] = recording.find("recordID").text
                    name = recording.find("metadata").find("name")
                    data["name"] = name.text if name is not None else None
                    data["participants"] = int(recording.find("participants").text)
                    data["playbacks"] = {}
                    playback = recording.find("playback")
                    if not playback:
                        continue

                    for format in playback.iter("format"):
                        images = []
                        preview = format.find("preview")
                        if preview is not None:
                            for i in (
                                format.find("preview").find("images").iter("image")
                            ):
                                image = {k: v for k, v in i.attrib.items()}
                                image["url"] = i.text
                                images.append(image)
                        type = format.find("type").text
                        if type in ("presentation", "video"):
                            data["playbacks"][type] = {
                                "url": format.find("url").text,
                                "images": images,
                            }
                    data["start_date"] = datetime.fromtimestamp(
                        int(recording.find("startTime").text) / 1000.0, tz=timezone.utc
                    ).replace(microsecond=0)
                    result.append(data)
            except Exception as exception:
                current_app.logger.error(exception)
        return result

    def update_recordings(self, recording_ids, metadata):
        """https://docs.bigbluebutton.org/dev/api.html#updaterecordings"""
        meta = {f"meta_{key}": value for (key, value) in metadata.items()}
        request = self.bbb_request(
            "updateRecordings", params={"recordID": ",".join(recording_ids), **meta}
        )
        return self.bbb_response(request)

    def prepare_request_to_join_bbb(self, meeting_role, fullname):
        """https://docs.bigbluebutton.org/dev/api.html#join"""
        params = {
            "fullName": fullname,
            "meetingID": self.meeting.meetingID,
            "redirect": "true",
        }
        if meeting_role == "attendee":
            params["role"] = "viewer"
            params["guest"] = "true"
        elif meeting_role == "authenticated":
            params["role"] = "viewer"
        elif meeting_role == "moderator":
            params["role"] = "moderator"

        return self.bbb_request("join", params=params)

    def end(self):
        """https://docs.bigbluebutton.org/development/api/#end"""
        request = self.bbb_request("end", params={"meetingID": self.meeting.meetingID})
        return self.bbb_response(request)

    def meeting_file_addition_xml(self, meeting_files):
        xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
        xml_end = " </module></modules>"
        xml_mid = ""
        for meeting_file in meeting_files:
            if meeting_file.url:
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
            else:  # file is not URL nor NC hence it was uploaded
                filehash = hashlib.sha1(
                    f"{current_app.config['SECRET_KEY']}-0-{meeting_file.id}-{current_app.config['SECRET_KEY']}".encode()
                ).hexdigest()
                url = url_for(
                    "meeting_files.ncdownload",
                    isexternal=0,
                    mfid=meeting_file.id,
                    mftoken=filehash,
                    _external=True,
                )
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{url}' filename='{meeting_file.title}' />"

        return xml_beg + xml_mid + xml_end
