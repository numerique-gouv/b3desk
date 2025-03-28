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
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
from flask import current_app
from flask import render_template
from flask import url_for

from b3desk.tasks import background_upload

from .. import BigBLueButtonUnavailable
from .. import cache
from .roles import Role


def cache_key(func, caller, prepped, *args, **kwargs):
    return prepped.url


def caching_exclusion(func, caller, prepped, *args, **kwargs):
    """Only read-only methods should be cached."""
    url = urlparse(prepped.url)
    endpoint_name = url.path.split("/")[-1]
    return prepped.method != "GET" or endpoint_name not in (
        "isMeetingRunning",
        "getMeetingInfo",
        "getMeetings",
        "getRecordings",
        "getRecordingTextTracks",
    )


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
                f"{current_app.config['BIGBLUEBUTTON_ENDPOINT']}/", ""
            ),
            bigbluebutton_secret,
        )
        checksum = hashlib.sha1(secret.encode("utf-8")).hexdigest()
        prepped.prepare_url(prepped.url, params={"checksum": checksum})
        return prepped

    @cache.memoize(
        unless=caching_exclusion,
        timeout=current_app.config["BIGBLUEBUTTON_API_CACHE_DURATION"],
    )
    def bbb_response(self, request):
        session = requests.Session()
        current_app.logger.debug(
            "BBB API request method:%s url:%s data:%s",
            request.method,
            request.url,
            request.body,
        )
        try:
            response = session.send(request)
        except requests.exceptions.ConnectionError:
            raise BigBLueButtonUnavailable
        current_app.logger.debug("BBB API response %s", response.text)
        return {c.tag: c.text for c in ElementTree.fromstring(response.content)}

    bbb_response.make_cache_key = cache_key

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
        if param := self.meeting.logoutUrl or current_app.config.get(
            "MEETING_LOGOUT_URL", ""
        ):
            params["logoutURL"] = str(param)
        if param := self.meeting.duration:
            params["duration"] = str(param)
        if param := self.meeting.voiceBridge:
            params["voiceBridge"] = str(param)

        # Pass the academy for statisticts purpose
        # https://github.com/numerique-gouv/b3desk/issues/80
        if self.meeting.user and self.meeting.user.mail_domain:
            params["meta_academy"] = self.meeting.user.mail_domain

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
                moderator_signin_url=self.meeting.get_signin_url(Role.moderator),
                attendee_link_introduction=quick_meeting_attendee_link_introduction,
                attendee_signin_url=self.meeting.get_signin_url(Role.attendee),
            )
        params["guestPolicy"] = (
            "ASK_MODERATOR" if self.meeting.guestPolicy else "ALWAYS_ACCEPT"
        )

        if not current_app.config["FILE_SHARING"]:
            request = self.bbb_request("create", params=params)
            data = self.bbb_response(request)
            return data

        # default file is sent right away since it is need as the background
        # image for the meeting
        # xml = (
        #     self.meeting_file_addition_xml([self.meeting.default_file])
        #     if self.meeting.default_file
        #     else None
        # )
        # TODO: xml as data is not sent anymore at BBB meeting creation to avoid delay
        request = self.bbb_request("create", "POST", params=params)
        data = self.bbb_response(request)
        # non default files are sent later
        if (
            self.meeting.files
            and "returncode" in data
            and data["returncode"] == "SUCCESS"
        ):
            xml = self.meeting_file_addition_xml(self.meeting.files)
            # TODO: send all files and not only the non default ones
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

    @cache.memoize(timeout=current_app.config["BIGBLUEBUTTON_API_CACHE_DURATION"])
    def get_recordings(self):
        """https://docs.bigbluebutton.org/development/api/#getrecordings"""
        request = self.bbb_request(
            "getRecordings", params={"meetingID": self.meeting.meetingID}
        )
        current_app.logger.debug(
            "BBB API request method:%s url:%s", request.method, request.url
        )
        try:
            response = requests.Session().send(request)
        except requests.exceptions.ConnectionError:
            raise BigBLueButtonUnavailable

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
                    data["start_date"] = datetime.fromtimestamp(
                        int(recording.find("startTime").text) / 1000.0, tz=timezone.utc
                    ).replace(microsecond=0)
                    data["end_date"] = datetime.fromtimestamp(
                        int(recording.find("endTime").text) / 1000.0, tz=timezone.utc
                    ).replace(microsecond=0)

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
                                "url": (media_url := format.find("url").text),
                                "images": images,
                            }
                            if type == "video":
                                data["playbacks"][type]["direct_link"] = (
                                    media_url + "video-0.m4v"
                                )
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
        if meeting_role == Role.attendee:
            params["role"] = "viewer"
            params["guest"] = "true"
        elif meeting_role == Role.authenticated:
            params["role"] = "viewer"
        elif meeting_role == Role.moderator:
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
                current_app.logger.info(
                    "Add document on BigBLueButton room %s %s creation for file %s",
                    self.meeting.name,
                    self.meeting.id,
                    meeting_file.title,
                )
                url = url_for(
                    "meeting_files.ncdownload",
                    isexternal=0,
                    mfid=meeting_file.id,
                    mftoken=filehash,
                    filename=meeting_file.title,
                    _external=True,
                    _scheme=current_app.config["PREFERRED_URL_SCHEME"],
                )
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{url}' filename='{meeting_file.title}' />"

        return xml_beg + xml_mid + xml_end
