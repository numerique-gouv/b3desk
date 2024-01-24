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
from b3desk.tasks import background_upload
from flask import current_app
from flask import render_template


class BBB:
    """Interface to BBB API."""

    def __init__(self, meeting):
        self.meeting = meeting

    def get_params_with_checksum(self, action, params):
        request = requests.Request(
            "GET",
            "{}/{}".format(current_app.config["BIGBLUEBUTTON_ENDPOINT"], action),
            params=params,
        )
        pr = request.prepare()
        bigbluebutton_secret = current_app.config["BIGBLUEBUTTON_SECRET"]
        s = "{}{}".format(
            pr.url.replace("?", "").replace(
                f'{current_app.config["BIGBLUEBUTTON_ENDPOINT"]}/', ""
            ),
            bigbluebutton_secret,
        )
        params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()
        return params

    def get_url(self, action):
        bbb_endpoint = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
        return f"{bbb_endpoint}/{action}"

    def is_meeting_running(self):
        action = "isMeetingRunning"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        r = requests.get(self.get_url(action), params=params)
        d = {c.tag: c.text for c in ElementTree.fromstring(r.content)}
        return d and d["returncode"] == "SUCCESS" and d["running"] == "true"

    def insertDocsNoDefault(self):
        # TODO: appears to be unused
        # meeting has started, we can now add files by using insertDocument API
        # ADDING ALL FILES EXCEPT DEFAULT
        SERVER_FQDN = current_app.config["SERVER_FQDN"]
        SECRET_KEY = current_app.config["SECRET_KEY"]
        BIGBLUEBUTTON_ENDPOINT = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
        BIGBLUEBUTTON_SECRET = current_app.config["BIGBLUEBUTTON_SECRET"]

        insertAction = "insertDocument"
        xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
        xml_end = " </module></modules>"
        xml_mid = ""
        for meeting_file in self.meeting.files:
            if meeting_file.is_default:
                continue
            elif meeting_file.url:
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
            else:  # file is not URL hence it was uploaded to nextcloud:
                filehash = hashlib.sha1(
                    f"{SECRET_KEY}-0-{meeting_file.id}-{SECRET_KEY}".encode()
                ).hexdigest()
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{SERVER_FQDN}/ncdownload/0/{meeting_file.id}/{filehash}' filename='{meeting_file.title}' />"

        xml = xml_beg + xml_mid + xml_end
        params = {"meetingID": self.meeting.meetingID}
        request = requests.Request(
            "POST",
            f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}",
            params=params,
        )
        pr = request.prepare()
        bigbluebutton_secret = BIGBLUEBUTTON_SECRET
        s = "{}{}".format(
            pr.url.replace("?", "").replace(BIGBLUEBUTTON_ENDPOINT + "/", ""),
            bigbluebutton_secret,
        )
        params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()

        requests.post(
            f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}",
            headers={"Content-Type": "application/xml"},
            data=xml,
            params=params,
        )
        return {}

    def create(self):
        action = "create"
        insertAction = "insertDocument"
        params = {
            "meetingID": self.meeting.meetingID,
            "name": self.meeting.name,
            "uploadExternalUrl": current_app.config["SERVER_FQDN"]
            + "/meeting/"
            + str(self.meeting.id)
            + "/externalUpload",
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

        params = self.get_params_with_checksum(action, params)
        if current_app.config["FILE_SHARING"]:
            # ADDING DEFAULT FILE TO MEETING
            SECRET_KEY = current_app.config["SECRET_KEY"]
            xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
            xml_end = " </module></modules>"
            xml_mid = ""

            if self.meeting.default_file:
                meeting_file = self.meeting.default_file
                if meeting_file.url:
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
                else:  # file is not URL nor NC hence it was uploaded
                    filehash = hashlib.sha1(
                        f"{SECRET_KEY}-0-{meeting_file.id}-{SECRET_KEY}".encode()
                    ).hexdigest()
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{current_app.config['SERVER_FQDN']}/ncdownload/0/{meeting_file.id}/{filehash}' filename='{meeting_file.title}' />"
            xml = xml_beg + xml_mid + xml_end
            r = requests.post(
                self.get_url(action),
                params=params,
                headers={"Content-Type": "application/xml"},
                data=xml,
            )
            ## BEGINNING OF TASK CELERY - aka background_upload for meeting_files
            params = {}
            xml = ""
            # ADDING ALL FILES EXCEPT DEFAULT
            SERVER_FQDN = current_app.config["SERVER_FQDN"]
            BIGBLUEBUTTON_ENDPOINT = current_app.config["BIGBLUEBUTTON_ENDPOINT"]
            BIGBLUEBUTTON_SECRET = current_app.config["BIGBLUEBUTTON_SECRET"]

            insertAction = "insertDocument"
            xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
            xml_end = " </module></modules>"
            xml_mid = ""
            for meeting_file in self.meeting.files:
                if meeting_file.is_default:
                    continue
                elif meeting_file.url:
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
                else:  # file is not URL nor NC hence it was uploaded
                    filehash = hashlib.sha1(
                        f"{SECRET_KEY}-0-{meeting_file.id}-{SECRET_KEY}".encode()
                    ).hexdigest()
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{SERVER_FQDN}/ncdownload/0/{meeting_file.id}/{filehash}' filename='{meeting_file.title}' />"

            xml = xml_beg + xml_mid + xml_end
            params = {"meetingID": self.meeting.meetingID}
            request = requests.Request(
                "POST",
                f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}",
                params=params,
            )
            pr = request.prepare()
            bigbluebutton_secret = BIGBLUEBUTTON_SECRET
            s = "{}{}".format(
                pr.url.replace("?", "").replace(f"{BIGBLUEBUTTON_ENDPOINT}/", ""),
                bigbluebutton_secret,
            )
            params["checksum"] = hashlib.sha1(s.encode("utf-8")).hexdigest()
            background_upload.delay(
                f"{BIGBLUEBUTTON_ENDPOINT}/{insertAction}", xml, params
            )

            d = {c.tag: c.text for c in ElementTree.fromstring(r.content)}
            return d
        else:
            r = requests.post(self.get_url(action), params=params)
            d = {c.tag: c.text for c in ElementTree.fromstring(r.content)}
            return d

    def delete_recordings(self, recording_ids):
        """DeleteRecordings BBB API: https://docs.bigbluebutton.org/dev/api.html#deleterecordings"""
        action = "deleteRecordings"
        params = self.get_params_with_checksum(action, {"recordID": recording_ids})
        response = requests.get(self.get_url(action), params=params)
        d = {
            child.tag: child.text for child in ElementTree.fromstring(response.content)
        }
        return d

    def get_meeting_info(self):
        # TODO: appears to be unused?
        action = "getMeetingInfo"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        resp = requests.get(self.get_url(action), params=params)
        return {c.tag: c.text for c in ElementTree.fromstring(resp.content)}

    def get_recordings(self):
        action = "getRecordings"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        response = requests.get(self.get_url(action), params=params)
        root = ElementTree.fromstring(response.content)
        return_code = root.find("returncode").text
        recordings = root.find("recordings")
        result = []
        if return_code != "FAILED" and recordings:
            try:
                for recording in recordings.iter("recording"):
                    d = {}
                    d["recordID"] = recording.find("recordID").text
                    name = recording.find("metadata").find("name")
                    d["name"] = name.text if name is not None else None
                    d["participants"] = int(recording.find("participants").text)
                    d["playbacks"] = {}
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
                            d["playbacks"][type] = {
                                "url": format.find("url").text,
                                "images": images,
                            }
                    d["start_date"] = datetime.fromtimestamp(
                        int(recording.find("startTime").text) / 1000.0, tz=timezone.utc
                    ).replace(microsecond=0)
                    result.append(d)
            except Exception as exception:
                current_app.logger.error(exception)
        return result

    def update_recordings(self, recording_ids, metadata):
        """updateRecordings BBB API: https://docs.bigbluebutton.org/dev/api.html#updaterecordings"""
        action = "updateRecordings"
        meta = {f"meta_{key}": value for (key, value) in metadata.items()}
        params = self.get_params_with_checksum(
            action, {"recordID": ",".join(recording_ids), **meta}
        )
        response = requests.get(self.get_url(action), params=params)
        d = {
            child.tag: child.text for child in ElementTree.fromstring(response.content)
        }
        return d

    def prepare_request_to_join_bbb(self, meeting_role, fullname):
        """Join BBB API: https://docs.bigbluebutton.org/dev/api.html#join"""
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
        action = "join"
        params = self.get_params_with_checksum(action, params)
        request = requests.Request("GET", self.get_url(action), params=params)
        pr = request.prepare()
        return pr

    def end(self):
        action = "end"
        params = self.get_params_with_checksum(
            action, {"meetingID": self.meeting.meetingID}
        )
        requests.get(self.get_url(action), params=params)
