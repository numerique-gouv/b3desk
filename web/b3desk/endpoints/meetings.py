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
from flask import Blueprint
from flask import abort
from flask import current_app
from flask import flash
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import lazy_gettext as _

from b3desk.forms import EndMeetingForm
from b3desk.forms import MeetingForm
from b3desk.forms import MeetingWithRecordForm
from b3desk.forms import RecordingForm
from b3desk.join import create_bbb_meeting
from b3desk.join import create_bbb_quick_meeting
from b3desk.join import get_join_url
from b3desk.join import get_signin_url
from b3desk.models import db
from b3desk.models.bbb import BBB
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import assign_unique_visio_code
from b3desk.models.meetings import get_quick_meeting_from_fake_id
from b3desk.models.meetings import save_voiceBridge_and_delete_meeting
from b3desk.models.meetings import unique_visio_code_generation
from b3desk.models.roles import Role
from b3desk.models.users import User
from b3desk.utils import check_oidc_connection

from .. import auth
from ..session import meeting_owner_needed

bp = Blueprint("meetings", __name__)


def meeting_mailto_params(meeting: Meeting, role: Role):
    """Generate mailto URL parameters for sharing meeting invitation links."""
    signin_url = get_signin_url(meeting, role)
    return render_template(
        "meeting/mailto/mail_href.txt",
        meeting=meeting,
        role=role,
        signin_url=signin_url,
    ).replace("\n", "%0D%0A")


@bp.route("/meeting/quick")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def quick_meeting():
    """Create and join a quick meeting for the authenticated user."""
    meeting = get_quick_meeting_from_fake_id()
    created = create_bbb_quick_meeting(meeting.fake_id, g.user)
    return redirect(
        get_join_url(
            meeting,
            Role.moderator,
            g.user.fullname,
            quick_meeting=True,
            waiting_room=not created,
        )
    )


@bp.route("/meeting/recordings/<meeting:meeting>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def show_meeting_recording(meeting: Meeting, owner: User):
    """Display the list of recordings for a meeting."""
    form = RecordingForm()
    return render_template(
        "meeting/recordings.html",
        meeting_mailto_params=meeting_mailto_params,
        meeting=meeting,
        form=form,
    )


@bp.route("/meeting/<meeting:meeting>/recordings/<recording_id>", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def update_recording_name(meeting: Meeting, recording_id, owner: User):
    """Update the name of a meeting recording."""
    form = RecordingForm(request.form)
    if not form.validate():
        abort(403)

    result = BBB(meeting.meetingID).update_recordings(
        recording_ids=[recording_id], metadata={"name": form.data["name"]}
    )
    if BBB.success(result):
        flash(_("Enregistrement renommé"), "success")
    else:
        flash(
            _(
                "Nous n'avons pas pu modifier cet enregistrement : {code}, {message}"
            ).format(
                code=result.get("returncode", ""),
                message=result.get("message", ""),
            ),
            "error",
        )
    return redirect(url_for("meetings.show_meeting_recording", meeting=meeting))


@bp.route("/meeting/new")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def new_meeting():
    """Display the form to create a new meeting."""
    if not g.user.can_create_meetings:
        flash(_("Vous n'avez pas le droit de créer de nouvelles réunions"), "error")
        return redirect(url_for("public.welcome"))

    form = MeetingWithRecordForm() if current_app.config["RECORDING"] else MeetingForm()

    return render_template(
        "meeting/wizard.html",
        meeting=None,
        form=form,
        recording=current_app.config["RECORDING"],
    )


@bp.route("/meeting/edit/<meeting:meeting>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def edit_meeting(meeting: Meeting, owner: User):
    """Display the form to edit an existing meeting."""
    form = (
        MeetingWithRecordForm(obj=meeting)
        if current_app.config["RECORDING"]
        else MeetingForm(obj=meeting)
    )
    return render_template(
        "meeting/wizard.html",
        meeting=meeting,
        form=form,
        recording=current_app.config["RECORDING"],
    )


@bp.route("/meeting/save", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def save_meeting():
    """Save a new or updated meeting from the meeting form submission."""
    form = (
        MeetingWithRecordForm(request.form)
        if current_app.config["RECORDING"]
        else MeetingForm(request.form)
    )

    is_new_meeting = not form.data["id"]
    if not g.user.can_create_meetings and is_new_meeting:
        flash(_("Vous n'avez pas le droit de créer de nouvelles réunions"), "error")
        return redirect(url_for("public.welcome"))

    if not form.validate():
        flash(_("Le formulaire contient des erreurs"), "error")
        return render_template(
            "meeting/wizard.html",
            meeting=None if is_new_meeting else db.session.get(Meeting, form.id.data),
            form=form,
            recording=current_app.config["RECORDING"],
        )

    if is_new_meeting:
        meeting = Meeting()
        meeting.user = g.user
    else:
        meeting_id = form.data["id"]
        meeting = db.session.get(Meeting, meeting_id)
        del form.id
        del form.name

    meeting.record = bool(
        form.data.get("allowStartStopRecording") or form.data.get("autoStartRecording")
    )
    updated_data = {
        key: form.data[key]
        for key in form.data
        if hasattr(meeting, key) and getattr(meeting, key) != form.data[key]
    }
    form.populate_obj(meeting)
    db.session.add(meeting)
    if not meeting.visio_code:
        assign_unique_visio_code(meeting)
    db.session.commit()
    if is_new_meeting:
        current_app.logger.info(
            "Meeting %s %s was created by %s",
            meeting.name,
            meeting.id,
            g.user.email,
        )
    else:
        current_app.logger.info(
            "Meeting %s %s was updated by %s. Updated fields : %s",
            meeting.name,
            meeting.id,
            g.user.email,
            updated_data,
        )
    flash(
        _("%(meeting_name)s modifications prises en compte", meeting_name=meeting.name),
        "success",
    )

    if BBB(meeting.meetingID).is_running():
        return render_template(
            "meeting/end.html",
            meeting=meeting,
            form=EndMeetingForm(data={"meeting_id": meeting_id}),
        )
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/end", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def end_meeting():
    """End the meeting on BBB.

    Called from EndMeetingForm.
    """
    form = EndMeetingForm(request.form)

    meeting_id = form.data["meeting_id"]
    meeting = db.session.get(Meeting, meeting_id) or abort(404)

    if g.user == meeting.user:
        data = BBB(meeting.meetingID).end()
        if BBB.success(data):
            flash(
                _("Réunion « %(meeting_name)s » terminée", meeting_name=meeting.name),
                "success",
            )
    else:
        flash(_("Vous ne pouvez pas terminer cette réunion"), "error")
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/create/<meeting:meeting>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_owner_needed
def create_meeting(meeting: Meeting, owner: User):
    """Create the meeting on BBB server."""
    create_bbb_meeting(meeting, g.user)
    db.session.commit()
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/delete", methods=["POST", "GET"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def delete_meeting():
    """Delete a meeting and all its associated files and recordings."""
    if request.method == "POST":
        meeting_id = request.form["id"]
        meeting = db.session.get(Meeting, meeting_id)

        if meeting.user_id == g.user.id:
            for meeting_file in meeting.files:
                db.session.delete(meeting_file)

            data = BBB(meeting.meetingID).delete_all_recordings()
            if data and not BBB.success(data):
                flash(
                    _(
                        "Nous n'avons pas pu supprimer les vidéos de cette réunion : {message}"
                    ).format(
                        message=data.get("message", ""),
                    ),
                    "error",
                )
            else:
                save_voiceBridge_and_delete_meeting(meeting)
                flash(_("Élément supprimé"), "success")
                current_app.logger.info(
                    "Meeting %s %s was deleted by %s",
                    meeting.name,
                    meeting.id,
                    g.user.email,
                )
        else:
            flash(_("Vous ne pouvez pas supprimer cet élément"), "error")
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/video/delete", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def delete_video_meeting():
    """Delete a specific recording from a meeting."""
    meeting_id = request.form["id"]
    meeting = db.session.get(Meeting, meeting_id)
    if meeting.user_id == g.user.id:
        recordID = request.form["recordID"]
        data = BBB(meeting.meetingID).delete_recordings(recordID)
        if BBB.success(data):
            flash(_("Vidéo supprimée"), "success")
            current_app.logger.info(
                "Meeting %s %s record %s was deleted by %s",
                meeting.name,
                meeting.id,
                recordID,
                g.user.email,
            )
        else:
            flash(
                _(
                    "Nous n'avons pas pu supprimer cette vidéo : %(code)s, %(message)s",
                    code=data.get("returncode", ""),
                    message=data.get("message", ""),
                ),
                "error",
            )
    else:
        flash(
            _("Vous ne pouvez pas supprimer cette enregistrement"),
            "error",
        )
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/favorite", methods=["POST"])
@auth.oidc_auth("default")
def meeting_favorite():
    """Toggle the favorite status of a meeting."""
    meeting_id = request.form["id"]
    meeting = db.session.get(Meeting, meeting_id)

    if meeting.user_id != g.user.id:
        abort(403)

    meeting.is_favorite = not meeting.is_favorite
    db.session.commit()

    return redirect(url_for("public.welcome", **request.args))


@bp.route("/meeting/available-visio-code", methods=["GET"])
@auth.oidc_auth("default")
def get_available_visio_code():
    """Generate and return an available unique visio code."""
    return jsonify(available_visio_code=unique_visio_code_generation())
