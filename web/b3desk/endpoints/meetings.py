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

from b3desk.forms import DelegationSearchForm
from b3desk.forms import MeetingForm
from b3desk.forms import MeetingWithRecordForm
from b3desk.forms import RecordingForm
from b3desk.join import create_bbb_meeting
from b3desk.join import create_bbb_quick_meeting
from b3desk.join import get_join_url
from b3desk.join import get_signin_url
from b3desk.models import db
from b3desk.models.bbb import BBB
from b3desk.models.meetings import AccessLevel
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingAccess
from b3desk.models.meetings import assign_unique_visio_code
from b3desk.models.meetings import get_meeting_access
from b3desk.models.meetings import get_quick_meeting_from_fake_id
from b3desk.models.meetings import save_voiceBridge_and_delete_meeting
from b3desk.models.meetings import unique_visio_code_generation
from b3desk.models.roles import Role
from b3desk.models.users import User
from b3desk.utils import check_oidc_connection

from .. import auth
from ..session import meeting_access_required
from ..utils import send_delegation_mail

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
@meeting_access_required(AccessLevel.DELEGATE)
def show_meeting_recording(meeting: Meeting, user: User):
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
@meeting_access_required(AccessLevel.DELEGATE)
def update_recording_name(meeting: Meeting, recording_id, user: User):
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


@bp.route("/meeting/new", methods=["GET", "POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
def new_meeting():
    """Display the form to create a new meeting and handle submission."""
    if not g.user.can_create_meetings:
        flash(_("Vous n'avez pas le droit de créer de nouvelles réunions"), "error")
        return redirect(url_for("public.welcome"))

    form = (
        MeetingWithRecordForm(request.form if request.method == "POST" else None)
        if current_app.config["RECORDING"]
        else MeetingForm(request.form if request.method == "POST" else None)
    )

    if request.method == "GET":
        return render_template(
            "meeting/wizard.html",
            meeting=None,
            form=form,
            recording=current_app.config["RECORDING"],
        )

    if not form.validate():
        flash(_("Le formulaire contient des erreurs"), "error")
        return render_template(
            "meeting/wizard.html",
            meeting=None,
            form=form,
            recording=current_app.config["RECORDING"],
        )

    meeting = Meeting()
    meeting.owner = g.user
    meeting.record = bool(
        form.data.get("allowStartStopRecording") or form.data.get("autoStartRecording")
    )
    form.populate_obj(meeting)
    db.session.add(meeting)
    assign_unique_visio_code(meeting)
    db.session.commit()
    current_app.logger.info(
        "Meeting %s %s was created by %s",
        meeting.name,
        meeting.id,
        g.user.email,
    )
    flash(
        _("{meeting_name} a bien été créé(e)").format(meeting_name=meeting.name),
        "success",
    )
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/edit/<meeting:meeting>", methods=["GET", "POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def edit_meeting(meeting: Meeting, user: User):
    """Display the form to edit an existing meeting and handle submission."""
    form = (
        MeetingWithRecordForm(
            request.form if request.method == "POST" else None, obj=meeting
        )
        if current_app.config["RECORDING"]
        else MeetingForm(
            request.form if request.method == "POST" else None, obj=meeting
        )
    )

    if request.method == "GET":
        return render_template(
            "meeting/wizard.html",
            meeting=meeting,
            form=form,
            recording=current_app.config["RECORDING"],
        )

    if not form.validate():
        flash(_("Le formulaire contient des erreurs"), "error")
        return render_template(
            "meeting/wizard.html",
            meeting=meeting,
            form=form,
            recording=current_app.config["RECORDING"],
        )

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
    current_app.logger.info(
        "Meeting %s %s was updated by %s. Updated fields : %s",
        meeting.name,
        meeting.id,
        user.email,
        updated_data,
    )
    flash(
        _("{meeting_name} modifications prises en compte").format(
            meeting_name=meeting.name
        ),
        "success",
    )

    if BBB(meeting.meetingID).is_running():
        return render_template(
            "meeting/end.html",
            meeting=meeting,
        )
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/<meeting:meeting>/end", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def end_meeting(meeting: Meeting, user: User):
    """End the meeting on BBB."""
    data = BBB(meeting.meetingID).end()
    if BBB.success(data):
        flash(
            f"{current_app.config['WORDING_MEETING'].capitalize()} « {meeting.name} » terminé(e)",
            "success",
        )
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/create/<meeting:meeting>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required()
def create_meeting(meeting: Meeting, user: User):
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

        if meeting.owner_id == g.user.id:
            for meeting_file in meeting.files:
                db.session.delete(meeting_file)

            data = BBB(meeting.meetingID).delete_all_recordings()
            if data and not BBB.success(data):
                flash(
                    _(
                        "Nous n'avons pas pu supprimer les vidéos de cette {meeting_label} : {message}"
                    ).format(
                        meeting_label=current_app.config["WORDINGS"]["meeting_label"],
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


@bp.route("/meeting/<meeting:meeting>/video/delete", methods=["POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required(AccessLevel.DELEGATE)
def delete_video_meeting(meeting: Meeting, user: User):
    """Delete a specific recording from a meeting."""
    recordID = request.form["recordID"]
    data = BBB(meeting.meetingID).delete_recordings(recordID)
    if BBB.success(data):
        flash(_("Vidéo supprimée"), "success")
        current_app.logger.info(
            "Meeting %s %s record %s was deleted by %s",
            meeting.name,
            meeting.id,
            recordID,
            user.email,
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
    return redirect(url_for("public.welcome"))


@bp.route("/meeting/favorite", methods=["POST"])
@auth.oidc_auth("default")
def meeting_favorite():
    """Toggle the favorite status of a meeting."""
    meeting_id = request.form["id"]
    meeting = db.session.get(Meeting, meeting_id)
    if g.user in meeting.favorite_of:
        meeting.favorite_of.remove(g.user)
    else:
        meeting.favorite_of.append(g.user)
    db.session.commit()

    return redirect(url_for("public.welcome", **request.args))


@bp.route("/meeting/available-visio-code", methods=["GET"])
@auth.oidc_auth("default")
def get_available_visio_code():
    """Generate and return an available unique visio code."""
    return jsonify(available_visio_code=unique_visio_code_generation())


@bp.route("/meeting/manage-delegation/<meeting:meeting>", methods=["GET", "POST"])
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required()
def manage_delegation(meeting: Meeting, user: User):
    """Display the page for manage meeting delegation."""
    form = DelegationSearchForm(request.form)
    if not request.form or not form.validate():
        return render_template(
            "meeting/delegation.html",
            meeting=meeting,
            form=form,
        )

    data = form.search.data
    new_delegate = (
        db.session.query(User)
        .filter(
            User.email == data,
            user.email != User.email,
        )
        .first()
    )

    if new_delegate is None:
        flash(_("L'utilisateur recherché n'existe pas"), "error")

    elif new_delegate in meeting.get_all_delegates:
        flash(_("L'utilisateur est déjà délégataire"), "warning")

    elif (
        len(meeting.get_all_delegates)
        >= current_app.config["MAXIMUM_MEETING_DELEGATES"]
    ):
        flash(
            _(
                "%(meeting_label)s ne peut plus recevoir de nouvelle délégation",
                meeting_label=current_app.config["WORDINGS"]["this_meeting"],
            ),
            "warning",
        )

    else:
        access = MeetingAccess(
            meeting_id=meeting.id,
            user_id=new_delegate.id,
            level=AccessLevel.DELEGATE,
        )
        db.session.add(access)
        db.session.commit()
        send_delegation_mail(meeting, new_delegate, new_delegation=True)
        flash(_("L'utilisateur a été ajouté aux délégataires"), "success")
        current_app.logger.info(
            "%s became delegate of meeting %s %s",
            new_delegate.email,
            meeting.id,
            meeting.name,
        )

    return render_template(
        "meeting/delegation.html",
        meeting=meeting,
        form=form,
    )


@bp.route("/meeting/remove-delegation/<meeting:meeting>/<user:delegate>")
@check_oidc_connection(auth)
@auth.oidc_auth("default")
@meeting_access_required()
def remove_delegate(meeting: Meeting, user: User, delegate: User):
    if delegate not in meeting.get_all_delegates:
        flash(_("L'utilisateur ne fait pas partie des délégataires"), "error")
    else:
        access = get_meeting_access(delegate.id, meeting.id)
        db.session.delete(access)
        db.session.commit()
        flash(_("L'utilisateur a été retiré des délégataires"), "success")
        send_delegation_mail(meeting, delegate, new_delegation=False)
        current_app.logger.info(
            "%s removed from delegates of meeting %s %s",
            delegate.email,
            meeting.id,
            meeting.name,
        )
    return redirect(url_for("meetings.manage_delegation", meeting=meeting))
