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
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import get_quick_meeting_from_fake_id
from b3desk.models.meetings import save_voiceBridge_and_delete_meeting
from b3desk.models.meetings import unique_visio_code_generation
from b3desk.models.roles import Role
from b3desk.models.users import User
from b3desk.utils import check_oidc_connection

from .. import auth
from ..session import meeting_owner_needed
from ..utils import is_accepted_email
from ..utils import is_valid_email
from ..utils import send_quick_meeting_mail

bp = Blueprint("meetings", __name__)


def meeting_mailto_params(meeting: Meeting, role: Role):
    """Generate mailto URL parameters for sharing meeting invitation links."""
    if role == Role.moderator:
        return render_template(
            "meeting/mailto/mail_href.txt", meeting=meeting, role=role
        ).replace("\n", "%0D%0A")
    elif role == Role.attendee:
        return render_template(
            "meeting/mailto/mail_href.txt", meeting=meeting, role=role
        ).replace("\n", "%0D%0A")


@bp.route("/meeting/mail", methods=["POST"])
def quick_mail_meeting():
    """Send a quick meeting invitation link to the provided email address."""
    #### Almost the same as quick meeting but we do not redirect to join
    email = request.form.get("mail")
    if not is_valid_email(email):
        flash(
            _(
                "Courriel invalide. Avez vous bien tapé votre email ? Vous pouvez réessayer."
            ),
            "error_login",
        )
        return redirect(url_for("public.index"))
    if not is_accepted_email(email):
        flash(
            _(
                "Ce courriel ne correspond pas à un service de l'État. Si vous appartenez à un service de l'État mais votre courriel n'est pas reconnu par Webinaire, contactez-nous pour que nous le rajoutions !"
            ),
            "error_login",
        )
        return redirect(url_for("public.index"))
    meeting = get_quick_meeting_from_fake_id()
    send_quick_meeting_mail(meeting, email)
    flash(_("Vous avez reçu un courriel pour vous connecter"), "success_login")
    return redirect(url_for("public.index"))


@bp.route("/meeting/quick")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def quick_meeting():
    """Create and join a quick meeting for the authenticated user."""
    meeting = get_quick_meeting_from_fake_id()
    created = meeting.create_bbb(g.user)
    return redirect(
        meeting.get_join_url(
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

    result = meeting.update_recording_name(recording_id, form.data["name"])
    return_code = result.get("returncode")
    if return_code == "SUCCESS":
        flash(_("Enregistrement renommé"), "success")
    else:
        message = result.get("message", "")
        flash(
            _(
                "Nous n'avons pas pu modifier cet enregistrement : {code}, {message}"
            ).format(code=return_code, message=message),
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
    meeting.visio_code = (
        meeting.visio_code if meeting.visio_code else unique_visio_code_generation()
    )
    meeting.save()
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
        _("{meeting_name} modifications prises en compte").format(
            meeting_name=meeting.name
        ),
        "success",
    )

    if meeting.is_running():
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
        meeting.end_bbb()
        flash(
            f"{current_app.config['WORDING_MEETING'].capitalize()} « {meeting.name} » terminé(e)",
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
    meeting.create_bbb(g.user)
    meeting.visio_code = (
        meeting.visio_code if meeting.visio_code else unique_visio_code_generation()
    )
    meeting.save()
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

            data = meeting.delete_all_recordings()
            return_code = data.get("returncode", "SUCCESS")
            if return_code != "SUCCESS":
                message = data.get("message", "")
                flash(
                    _(
                        "Nous n'avons pas pu supprimer les vidéos de cette {meeting_label} : {message}"
                    ).format(
                        meeting_label=current_app.config["WORDINGS"]["meeting_label"],
                        message=message,
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
        data = meeting.delete_recordings(recordID)
        return_code = data.get("returncode")
        if return_code == "SUCCESS":
            flash(_("Vidéo supprimée"), "success")
            current_app.logger.info(
                "Meeting %s %s record %s was deleted by %s",
                meeting.name,
                meeting.id,
                recordID,
                g.user.email,
            )
        else:
            message = data.get("message", "")
            flash(
                _(
                    "Nous n'avons pas pu supprimer cette vidéo : %(code)s, %(message)s",
                    code=return_code,
                    message=message,
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
    meeting.save()

    return redirect(url_for("public.welcome", **request.args))


@bp.route("/meeting/available-visio-code", methods=["GET"])
@auth.oidc_auth("default")
def get_available_visio_code():
    """Generate and return an available unique visio code."""
    return jsonify(available_visio_code=unique_visio_code_generation())
