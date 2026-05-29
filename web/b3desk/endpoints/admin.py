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
from b3desk.forms import MemberSearchForm
from b3desk.forms import UserSearchForm
from b3desk.models import db
from b3desk.models.groups import Group
from b3desk.models.meetings import Meeting
from b3desk.models.users import User

from ..session import admin_needed

bp = Blueprint("admin", __name__)


MAX_PER_PAGE = 50


def get_groups_paginate(max_per_page, data):
    query = db.select(Group).order_by(Group.created_at)
    if data:
        query = query.where(
            or_(
                Group.id == int(data) if data.isdigit() else None,
                Group.name.ilike(f"%{data}%"),
            )
        )
    return db.paginate(query, max_per_page=max_per_page)


def get_meetings_paginate(max_per_page, data):
    query = db.select(Meeting).order_by(Meeting.created_at)
    if data:
        query = query.where(
            or_(
                Meeting.id == int(data) if data.isdigit() else None,
                Meeting.name.ilike(f"%{data}%"),
                Meeting.visio_code == data,
            )
        )
    return db.paginate(query, max_per_page=max_per_page)


def get_users_paginate(max_per_page, data=None):
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
    return db.paginate(query, max_per_page=max_per_page)


@bp.route("/admin/home")
@admin_needed
def home():
    """Display the menu of admin page."""
    return render_template(
        "admin/home.html",
    )


@bp.route("/admin/users", methods=["GET", "POST"])
@admin_needed
def manage_users():
    """Display user list to manage users of admin page."""
    form = UserSearchForm(request.form)
    if not request.form or not form.validate():
        users_page = get_users_paginate(max_per_page=MAX_PER_PAGE, data=None)
        return render_template(
            "admin/users.html",
            admin_mode=True,
            users_page=users_page,
            form=form,
            data=None,
        )
    data = form.search.data.lower()
    users_page = get_users_paginate(max_per_page=MAX_PER_PAGE, data=data)
    return render_template(
        "admin/users.html",
        admin_mode=True,
        users_page=users_page,
        form=form,
        data=data,
    )


@bp.route("/admin/meetings", methods=["GET", "POST"])
@admin_needed
def manage_meetings():
    """Display meeting list to manage meetings of admin page."""
    form = MeetingSearchForm(request.form)
    if not request.form or not form.validate():
        meetings_page = get_meetings_paginate(max_per_page=MAX_PER_PAGE, data=None)
        return render_template(
            "admin/meetings.html",
            admin_mode=True,
            meetings_page=meetings_page,
            form=form,
            data=None,
        )
    data = form.search.data.lower()
    meetings_page = get_meetings_paginate(max_per_page=MAX_PER_PAGE, data=data)
    return render_template(
        "admin/meetings.html",
        admin_mode=True,
        meetings_page=meetings_page,
        form=form,
        data=data,
    )


@bp.route("/admin/user/<user:user>")
@admin_needed
def user_infos(user: User):
    """Display user infos of admin page."""
    return render_template(
        "admin/selected_user.html",
        admin_mode=True,
        selected_user=user,
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
    return redirect(url_for("admin.home"))


@bp.route("/admin/groups", methods=["GET", "POST"])
@admin_needed
def manage_groups():
    """Display group list to manage groups of admin page."""
    form = GroupSearchForm(request.form)
    if not request.form or not form.validate():
        groups_page = get_groups_paginate(max_per_page=MAX_PER_PAGE, data=None)
        return render_template(
            "admin/groups.html",
            groups_page=groups_page,
            form=form,
            data=None,
        )
    data = form.search.data.lower()
    groups_page = get_groups_paginate(max_per_page=MAX_PER_PAGE, data=data)
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

    del form.id

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

    return redirect(url_for("admin.home"))


@bp.route("/admin/manage-group-members/<group:group>", methods=["GET", "POST"])
@admin_needed
def manage_group_members(group: Group):
    """Display group members list and member addition of admin page."""
    form = MemberSearchForm(request.form if request.method == "POST" else None)
    if not request.form or not form.validate():
        return render_template(
            "admin/group_members.html",
            group=group,
            form=form,
        )

    data = form.search.data.lower()
    new_member = (
        db.session.query(User)
        .filter(
            User.email == data,
        )
        .first()
    )

    if new_member is None:
        flash(_("L'utilisateur recherché n'existe pas"), "error")

    elif new_member in group.members:
        flash(_("L'utilisateur est déjà dans le groupe"), "warning")

    else:
        group.members.append(new_member)
        db.session.commit()
        flash(_("L'utilisateur a été ajouté au groupe"), "success")
        current_app.logger.info(
            "%s became member of group %s %s",
            new_member.email,
            group.id,
            group.name,
        )

    return render_template(
        "admin/group_members.html",
        group=group,
        form=form,
    )


@bp.route("/admin/manage-group-members/<group:group>/<user:member>")
@admin_needed
def remove_member(group: Group, member: User):
    """Display group members list and member removing admin page."""
    form = MemberSearchForm()
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
    return render_template(
        "admin/group_members.html",
        group=group,
        form=form,
    )


@bp.route("/admin/delete-group/<group:group>")
@admin_needed
def delete_group(group: Group):
    """Display group deletion of admin page."""
    return render_template(
        "admin/delete_group.html",
        group=group,
    )


@bp.route("/admin/confirm-delete-group/<group:group>")
@admin_needed
def confirm_delete_group(group: Group):
    """Display group deletion of admin page."""
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for("admin.manage_groups"))
