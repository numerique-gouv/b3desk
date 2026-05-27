from flask import Blueprint
from flask import render_template
from flask import request

from b3desk.forms import MeetingSearchForm
from b3desk.forms import UserSearchForm
from b3desk.models.meetings import get_meetings_paginate
from b3desk.models.users import User
from b3desk.models.users import get_users_paginate

from ..session import admin_needed

bp = Blueprint("admin", __name__)


MAX_PER_PAGE = 3


@bp.route("/admin/home")
@admin_needed
def home():
    return render_template(
        "admin/home.html",
        admin_mode=True,
        users_page=None,
        meetings_page=None,
        selected_user=None,
    )


@bp.route("/admin/users", methods=["GET", "POST"])
@admin_needed
def manage_users():
    form = UserSearchForm(request.form)
    if not request.form or not form.validate():
        users_page = get_users_paginate(max_per_page=MAX_PER_PAGE, data=None)
        return render_template(
            "admin/home.html",
            admin_mode=True,
            users_page=users_page,
            meetings_page=None,
            selected_user=None,
            form=form,
            data=None,
        )
    data = form.search.data.lower()
    users_page = get_users_paginate(max_per_page=MAX_PER_PAGE, data=data)
    return render_template(
        "admin/home.html",
        admin_mode=True,
        users_page=users_page,
        meetings_page=None,
        selected_user=None,
        form=form,
        data=data,
    )


@bp.route("/admin/meetings", methods=["GET", "POST"])
@admin_needed
def manage_meetings():
    form = MeetingSearchForm(request.form)
    if not request.form or not form.validate():
        meetings_page = get_meetings_paginate(max_per_page=MAX_PER_PAGE, data=None)
        return render_template(
            "admin/home.html",
            admin_mode=True,
            users_page=None,
            meetings_page=meetings_page,
            selected_user=None,
            form=form,
            data=None,
        )
    data = form.search.data.lower()
    meetings_page = get_meetings_paginate(max_per_page=MAX_PER_PAGE, data=data)
    return render_template(
        "admin/home.html",
        admin_mode=True,
        users_page=None,
        meetings_page=meetings_page,
        selected_user=None,
        form=form,
        data=data,
    )


@bp.route("/admin/user/<user:user>")
@admin_needed
def user_infos(user: User):
    return render_template(
        "admin/home.html",
        admin_mode=True,
        users_page=None,
        meetings_page=None,
        selected_user=user,
    )
