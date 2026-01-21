# +----------------------------------------------------------------------------+
# | B3DESK                                                                  |
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
from flask import url_for

from b3desk.tasks import background_upload

from .. import BigBlueButtonUnavailable
from .. import cache
from .roles import Role


def cache_key(func, caller, prepped, *args, **kwargs):
    """Generate a cache key based on the request URL."""
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

    @classmethod
    def success(cls, payload):
        return payload and payload.get("returncode") == "SUCCESS"

    def __init__(self, meeting_id):
        self.meeting_id = meeting_id

    def _send_request(self, request):
        """Send an HTTP request and parse the XML response.

        Raises BigBlueButtonUnavailable on network/parsing errors.
        """
        session = requests.Session()
        if current_app.debug:  # pragma: no cover
            session.verify = False

        current_app.logger.debug(
            "BBB API request method:%s url:%s data:%s",
            request.method,
            request.url,
            request.body,
        )
        try:
            response = session.send(
                request,
                timeout=current_app.config[
                    "BIGBLUEBUTTON_REQUEST_TIMEOUT"
                ].total_seconds(),
            )
        except requests.Timeout as err:
            current_app.logger.warning("BBB API timeout error %s", err)
            raise BigBlueButtonUnavailable() from err
        except requests.exceptions.ConnectionError as err:
            current_app.logger.warning("BBB API connection error %s", err)
            raise BigBlueButtonUnavailable() from err

        current_app.logger.debug("BBB API response %s", response.text)

        try:
            root = ElementTree.fromstring(response.content)
        except ElementTree.ParseError as err:
            current_app.logger.warning("BBB API XML parse error %s", err)
            raise BigBlueButtonUnavailable() from err

        returncode_elem = root.find("returncode")
        if returncode_elem is None:
            current_app.logger.warning("BBB API response missing returncode")
            raise BigBlueButtonUnavailable()

        return root

    def bbb_request(self, action, method="GET", **kwargs):
        """Prepare a BBB API request with authentication checksum."""
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
        """Send the BBB API request and parse the XML response."""
        root = self._send_request(request)
        return {c.tag: c.text for c in root}

    bbb_response.make_cache_key = cache_key

    def is_running(self):
        """Check if the meeting is running.

        https://docs.bigbluebutton.org/development/api/#ismeetingrunning
        """
        request = self.bbb_request(
            "isMeetingRunning", params={"meetingID": self.meeting_id}
        )
        data = self.bbb_response(request)
        return self.success(data) and data["running"] == "true"

    def create(
        self,
        *,
        name,
        record=None,
        auto_start_recording=None,
        allow_start_stop_recording=None,
        webcams_only_for_moderator=None,
        mute_on_start=None,
        lock_settings_disable_cam=None,
        lock_settings_disable_mic=None,
        allow_mods_to_unmute_users=None,
        lock_settings_disable_private_chat=None,
        lock_settings_disable_public_chat=None,
        lock_settings_disable_note=None,
        attendee_pw=None,
        moderator_pw=None,
        welcome=None,
        max_participants=None,
        logout_url=None,
        duration=None,
        voice_bridge=None,
        guest_policy=None,
        presentation_upload_external_url=None,
        presentation_upload_external_description=None,
        moderator_only_message=None,
        meta_academy=None,
        analytics_callback_url=None,
    ):
        """Create a new meeting.

        https://docs.bigbluebutton.org/development/api/#create.
        """
        params = {
            "meetingID": self.meeting_id,
            "name": name,
        }
        if presentation_upload_external_url:
            params["presentationUploadExternalUrl"] = presentation_upload_external_url
            params["presentationUploadExternalDescription"] = (
                presentation_upload_external_description
            )
        if record is not None:
            params["record"] = str(record).lower()
        if auto_start_recording is not None:
            params["autoStartRecording"] = str(auto_start_recording).lower()
        if allow_start_stop_recording is not None:
            params["allowStartStopRecording"] = str(allow_start_stop_recording).lower()
        if webcams_only_for_moderator is not None:
            params["webcamsOnlyForModerator"] = str(webcams_only_for_moderator).lower()
        if mute_on_start is not None:
            params["muteOnStart"] = str(mute_on_start).lower()
        if lock_settings_disable_cam is not None:
            params["lockSettingsDisableCam"] = str(lock_settings_disable_cam).lower()
        if lock_settings_disable_mic is not None:
            params["lockSettingsDisableMic"] = str(lock_settings_disable_mic).lower()
        if allow_mods_to_unmute_users is not None:
            params["allowModsToUnmuteUsers"] = str(allow_mods_to_unmute_users).lower()
        if lock_settings_disable_private_chat is not None:
            params["lockSettingsDisablePrivateChat"] = str(
                lock_settings_disable_private_chat
            ).lower()
        if lock_settings_disable_public_chat is not None:
            params["lockSettingsDisablePublicChat"] = str(
                lock_settings_disable_public_chat
            ).lower()
        if lock_settings_disable_note is not None:
            params["lockSettingsDisableNote"] = str(lock_settings_disable_note).lower()
        if attendee_pw:
            params["attendeePW"] = attendee_pw
        if moderator_pw:
            params["moderatorPW"] = moderator_pw
        if welcome:
            params["welcome"] = welcome
        if max_participants:
            params["maxParticipants"] = str(max_participants)
        if logout_url:
            params["logoutURL"] = str(logout_url)
        if duration:
            params["duration"] = str(duration)
        if voice_bridge:
            params["voiceBridge"] = str(voice_bridge)
        if meta_academy:
            params["meta_academy"] = meta_academy
        if analytics_callback_url:
            params.update(
                {
                    "meetingKeepEvents": "true",
                    "meta_analytics-callback-url": str(analytics_callback_url),
                }
            )
        if moderator_only_message:
            params["moderatorOnlyMessage"] = moderator_only_message
        params["guestPolicy"] = "ASK_MODERATOR" if guest_policy else "ALWAYS_ACCEPT"

        if not current_app.config["FILE_SHARING"]:
            request = self.bbb_request("create", params=params)
            return self.bbb_response(request)

        request = self.bbb_request("create", "POST", params=params)
        return self.bbb_response(request)

    def delete_recordings(self, recording_ids):
        """Delete recordings.

        https://docs.bigbluebutton.org/dev/api.html#deleterecordings
        """
        request = self.bbb_request(
            "deleteRecordings", params={"recordID": recording_ids}
        )
        return self.bbb_response(request)

    def delete_all_recordings(self):
        """Delete all recordings for this meeting."""
        recordings = self.get_recordings()
        if not recordings:
            return {}
        recording_ids = ",".join(
            [recording.get("recordID", "") for recording in recordings]
        )
        return self.delete_recordings(recording_ids)

    def get_meeting_info(self):
        """Retrieve metadata about a meeting.

        https://docs.bigbluebutton.org/development/api/#getmeetinginfo
        """
        request = self.bbb_request(
            "getMeetingInfo", params={"meetingID": self.meeting_id}
        )
        return self.bbb_response(request)

    @cache.memoize(timeout=current_app.config["BIGBLUEBUTTON_API_CACHE_DURATION"])
    def get_recordings(self):
        """Get the list of recordings for a meeting.

        https://docs.bigbluebutton.org/development/api/#getrecordings
        """
        request = self.bbb_request(
            "getRecordings", params={"meetingID": self.meeting_id}
        )
        root = self._send_request(request)
        data = {c.tag: c.text for c in root}
        if not self.success(data):
            return []

        recordings = root.find("recordings")
        if recordings is None:
            return []

        result = []
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
                if playback is None:
                    continue

                for format in playback.iter("format"):
                    images = []
                    preview = format.find("preview")
                    if preview is not None:
                        for i in format.find("preview").find("images").iter("image"):
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
        """Update the recordings of a meeting.

        https://docs.bigbluebutton.org/dev/api.html#updaterecordings
        """
        meta = {f"meta_{key}": value for (key, value) in metadata.items()}
        request = self.bbb_request(
            "updateRecordings", params={"recordID": ",".join(recording_ids), **meta}
        )
        return self.bbb_response(request)

    def prepare_request_to_join_bbb(self, meeting_role, fullname):
        """Join a BBB meeting.

        https://docs.bigbluebutton.org/dev/api.html#join
        """
        params = {
            "fullName": fullname,
            "meetingID": self.meeting_id,
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
        """Close a BBB meeting.

        https://docs.bigbluebutton.org/development/api/#end
        """
        request = self.bbb_request("end", params={"meetingID": self.meeting_id})
        return self.bbb_response(request)

    def send_meeting_files(self, meeting_files):
        """Send files to a BBB meeting."""
        from .meetings import MeetingFiles
        from .meetings import get_meeting_file_hash

        xml_beg = "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> "
        xml_end = " </module></modules>"
        xml_mid = ""
        for meeting_file in meeting_files:
            isexternal = not isinstance(meeting_file, MeetingFiles)
            if not isexternal and meeting_file.url:
                xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{meeting_file.url}' filename='{meeting_file.title}' />"
            else:  # file is not URL nor NC hence it was uploaded
                token = get_meeting_file_hash(
                    meeting_file.owner.id, meeting_file.nc_path
                )
                current_app.logger.info(
                    "Add document on BigBlueButton room %s creation for file %s",
                    self.meeting_id,
                    meeting_file.title,
                )
                url = url_for(
                    "meeting_files.ncdownload",
                    token=token,
                    user=meeting_file.owner,
                    ncpath=meeting_file.nc_path,
                    _external=True,
                    _scheme=current_app.config["PREFERRED_URL_SCHEME"],
                )
                if not isexternal:
                    xml_mid += f"<document downloadable='{'true' if meeting_file.is_downloadable else 'false'}' url='{url}' filename='{meeting_file.title}' />"
                else:
                    xml_mid += (
                        f"<document url='{url}' filename='{meeting_file.title}' />"
                    )
        payload = xml_beg + xml_mid + xml_end

        request = self.bbb_request(
            "insertDocument", params={"meetingID": self.meeting_id}
        )
        background_upload.delay(request.url, payload)
