from flask import Blueprint
from flask import current_app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import lazy_gettext as _
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from b3desk.forms import GroupForm
from b3desk.forms import GroupSearchForm
from b3desk.forms import MeetingSearchForm
from b3desk.forms import UserSearchForm
from b3desk.join import get_signin_url
from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.roles import Role
from b3desk.models.users import User

from ..session import admin_needed

bp = Blueprint("admin", __name__)


PER_PAGE = 50


def get_groups_paginate(per_page, data):
    query = db.select(Group).order_by(Group.created_at)
    if data:
        query = query.where(
            or_(
                Group.id == int(data) if data.isdigit() else None,
                Group.name.ilike(f"%{data}%"),
            )
        )
    return db.paginate(query, per_page=per_page)


def get_meetings_paginate(per_page, data):
    query = db.select(Meeting).order_by(Meeting.created_at)
    if data:
        query = query.where(
            or_(
                Meeting.id == int(data) if data.isdigit() else None,
                Meeting.name.ilike(f"%{data}%"),
                Meeting.visio_code == data,
            )
        )
    return db.paginate(query, per_page=per_page)


def get_group_members_paginate(group, per_page, data=None):
    members = group.get_all_members
    if data:
        members = members.where(
            or_(
                User.id == int(data) if data.isdigit() else None,
                User.given_name.ilike(f"%{data}%"),
                User.family_name.ilike(f"%{data}%"),
                User.email.ilike(f"%{data}%"),
            )
        )
    return db.paginate(members, per_page=per_page)


def get_users_paginate(per_page, data=None):
    query = db.select(User).order_by(User.created_at)
    if data:
        query = query.where(
            or_(
                User.id == int(data) if data.isdigit() else None,
                User.given_name.ilike(f"%{data}%"),
                User.family_name.ilike(f"%{data}%"),
                User.email.ilike(f"%{data}%"),
            )
        )
    return db.paginate(query, per_page=per_page)


@bp.route("/admin/home")
@admin_needed
def home():
    """Display the menu of admin page."""
    return render_template(
        "admin/home.html",
    )


@bp.route("/admin/users")
@admin_needed
def manage_users():
    """Display user list to manage users."""
    form = UserSearchForm(request.args)
    data = form.search.data.lower() if form.search.data else None
    users_page = get_users_paginate(per_page=PER_PAGE, data=data)
    return render_template(
        "admin/users.html",
        admin_mode=True,
        users_page=users_page,
        form=form,
        data=data,
        group=None,
        add_members=False,
    )


@bp.route("/admin/user/<user:user>")
@admin_needed
def user_infos(user: User):
    """Display user infos."""
    return render_template(
        "admin/user_infos.html",
        admin_mode=True,
        user=user,
    )


@bp.route("/admin/meetings")
@admin_needed
def manage_meetings():
    """Display meeting list to manage meetings."""
    form = MeetingSearchForm(request.args)
    data = form.search.data.lower() if form.search.data else None
    meetings_page = get_meetings_paginate(per_page=PER_PAGE, data=data)
    return render_template(
        "admin/meetings.html",
        admin_mode=True,
        meetings_page=meetings_page,
        form=form,
        data=data,
    )


@bp.route("/admin/meeting/<meeting:meeting>")
@admin_needed
def meeting_infos(meeting: Meeting):
    """Display meeting infos of admin page."""
    meeting.moderator_url = get_signin_url(meeting, Role.moderator)
    meeting.attendee_url = get_signin_url(meeting, Role.attendee)
    meeting.authenticated_url = get_signin_url(meeting, Role.authenticated)
    return render_template(
        "admin/meeting_infos.html",
        admin_mode=True,
        meeting=meeting,
    )


@bp.route("/admin/create-group", methods=["GET", "POST"])
@admin_needed
def create_group():
    """Display group creation of admin page."""
    form = GroupForm(request.form)
    if not request.form or not form.validate():
        return render_template(
            "admin/group_form.html",
            group=None,
            form=form,
            data=None,
        )
    group = Group()
    form.populate_obj(group)
    db.session.add(group)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        form.name.errors.append(_("Ce nom est déjà utilisé."))
        return render_template(
            "admin/group_form.html",
            group=None,
            form=form,
            data=None,
        )

    current_app.logger.info(
        "Group %s %s was created by %s",
        group.name,
        group.id,
        g.user.email,
    )
    flash(
        _("{group_name} a bien été créé(e)").format(group_name=group.name),
        "success",
    )
    return redirect(url_for("admin.group_infos", group=group))


@bp.route("/admin/group/<group:group>")
@admin_needed
def group_infos(group: Group):
    """Display group infos of admin page."""
    return render_template(
        "admin/group_infos.html",
        group=group,
    )


@bp.route("/admin/groups", methods=["GET", "POST"])
@admin_needed
def manage_groups():
    """Display group list to manage groups of admin page."""
    form = GroupSearchForm(request.form)
    if not request.form or not form.validate():
        groups_page = get_groups_paginate(per_page=PER_PAGE, data=None)
        return render_template(
            "admin/groups.html",
            groups_page=groups_page,
            form=form,
            data=None,
        )
    data = form.search.data.lower()
    groups_page = get_groups_paginate(per_page=PER_PAGE, data=data)
    return render_template(
        "admin/groups.html",
        groups_page=groups_page,
        form=form,
        data=data,
    )


@bp.route("/admin/edit-group/<group:group>", methods=["GET", "POST"])
@admin_needed
def edit_group(group: Group):
    """Display group settings for group edition of admin page."""
    form = GroupForm(request.form if request.method == "POST" else None, obj=group)
    if request.method == "GET":
        return render_template(
            "admin/group_form.html",
            form=form,
            group=group,
        )

    if not form.validate():
        flash(_("Le formulaire contient des erreurs"), "error")
        return render_template(
            "admin/group_form.html",
            form=form,
            group=group,
        )

    updated_data = {
        key: form.data[key]
        for key in form.data
        if hasattr(group, key) and getattr(group, key) != form.data[key]
    }
    form.populate_obj(group)
    db.session.add(group)
    db.session.commit()
    current_app.logger.info(
        "Group %s %s was updated by %s. Updated fields : %s",
        group.name,
        group.id,
        g.user.email,
        updated_data,
    )
    flash(
        _("%(group_name)s modifications prises en compte", group_name=group.name),
        "success",
    )

    return redirect(url_for("admin.group_infos", group=group))


@bp.route("/admin/manage-group-members/<group:group>", methods=["GET", "POST"])
@admin_needed
def manage_group_members(group: Group):
    """Display group members list and member addition of admin page."""
    form = UserSearchForm(request.args)
    data = form.search.data.lower() if form.search.data else None
    members_page = get_group_members_paginate(group, per_page=PER_PAGE, data=data)
    return render_template(
        "admin/group_members.html",
        group=group,
        form=form,
        members_page=members_page,
        data=data,
        add_members=False,
    )


@bp.route("/admin/manage-group-members/<group:group>/<user:member>", methods=["POST"])
@admin_needed
def remove_member(group: Group, member: User):
    """Remove a member from the group."""
    form = UserSearchForm(request.args)
    data = form.search.data.lower() if form.search.data else None
    if member not in group.members:
        flash(_("L'utilisateur ne fait pas partie du groupe"), "error")
    else:
        group.members.remove(member)
        db.session.commit()
        flash(_("L'utilisateur a été retiré du groupe"), "success")
        current_app.logger.info(
            "%s member removed from group %s %s",
            member.email,
            group.id,
            group.name,
        )
    return redirect(url_for("admin.manage_group_members", group=group, search=data))


@bp.route("/admin/delete-group/<group:group>")
@admin_needed
def delete_group(group: Group):
    """Display group deletion of admin page."""
    return render_template(
        "admin/delete_group.html",
        group=group,
    )


@bp.route("/admin/confirm-delete-group/<group:group>", methods=["POST"])
@admin_needed
def confirm_delete_group(group: Group):
    """Delete a group."""
    db.session.delete(group)
    db.session.commit()
    flash(_("Le groupe a été supprimé"), "success")
    current_app.logger.info("Groupe %s %s deleted", group.id, group.name)
    return redirect(url_for("admin.manage_groups"))


@bp.route("/admin/add-group-members/<group:group>")
@admin_needed
def add_group_members_page(group: Group):
    """Display non member users list to add members."""
    form = UserSearchForm(request.args)
    data = form.search.data.lower() if form.search.data else None
    users_page = get_users_paginate(per_page=PER_PAGE, data=data)
    return render_template(
        "admin/add_group_members_page.html",
        group=group,
        form=form,
        users_page=users_page,
        data=data,
        add_members=True,
    )


@bp.route("/admin/add-group-members/<group:group>/<user:user>", methods=["POST"])
@admin_needed
def add_group_members(group: Group, user: User):
    """Add a member to the group."""
    form = UserSearchForm(request.args)
    data = form.search.data.lower() if form.search.data else None
    if user in group.members:
        flash(_("L'utilisateur est déjà dans le groupe"), "error")
    else:
        group.members.append(user)
        db.session.commit()
        flash(_("L'utilisateur a été ajouté au groupe"), "success")
        current_app.logger.info(
            "%s became member of group %s %s",
            user.email,
            group.id,
            group.name,
        )
    return redirect(url_for("admin.add_group_members_page", group=group, search=data))
