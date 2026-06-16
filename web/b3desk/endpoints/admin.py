from flask import Blueprint
from flask import render_template
from flask import request
from sqlalchemy import or_

from b3desk.forms import MeetingSearchForm
from b3desk.forms import UserSearchForm
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.users import User

from ..session import admin_needed

bp = Blueprint("admin", __name__)


MAX_PER_PAGE = 50


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


@bp.route("/admin/users")
@admin_needed
def manage_users():
    """Display user list to manage users."""
    form = UserSearchForm(request.args, meta={"csrf": False})
    data = form.search.data.lower() if form.search.data else None
    users_page = get_users_paginate(max_per_page=MAX_PER_PAGE, data=data)
    return render_template(
        "admin/users.html",
        admin_mode=True,
        users_page=users_page,
        form=form,
        data=data,
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
    form = MeetingSearchForm(request.args, meta={"csrf": False})
    data = form.search.data.lower() if form.search.data else None
    meetings_page = get_meetings_paginate(max_per_page=MAX_PER_PAGE, data=data)
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
    """Display meeting infos."""
    return render_template(
        "admin/meeting_infos.html",
        admin_mode=True,
        meeting=meeting,
    )
