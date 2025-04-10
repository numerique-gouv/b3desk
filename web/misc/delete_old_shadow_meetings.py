from b3desk.models.meetings import get_all_old_shadow_meetings
from b3desk.models.meetings import save_voiceBridge_and_delete_meeting

meetings = get_all_old_shadow_meetings()
for meeting in meetings:
    save_voiceBridge_and_delete_meeting(meeting)
