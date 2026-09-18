from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Unicode
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from b3desk.utils import utcnow

from . import db

if TYPE_CHECKING:
    from .users import User

group_member_table = db.Table(
    "group_member",
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("group_id", ForeignKey("group.id"), primary_key=True),
)

excludelist_table = db.Table(
    "excludelist",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("group.id"), primary_key=True),
)


class Group(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    name: Mapped[str | None] = mapped_column(Unicode(150), unique=True)
    enable_sip: Mapped[bool | None] = mapped_column(default=None)
    enable_file_sharing: Mapped[bool | None] = mapped_column(default=None)
    enable_ai_summary: Mapped[bool | None] = mapped_column(default=None)
    academic_codes: Mapped[list] = mapped_column(
        MutableList.as_mutable(db.JSON), default=list
    )
    mail_domains: Mapped[list] = mapped_column(
        MutableList.as_mutable(db.JSON), default=list
    )

    members: Mapped[list[User]] = relationship(
        secondary=group_member_table, back_populates="groups"
    )
    excluded_users = db.relationship(
        "User", secondary=excludelist_table, back_populates="excluded_groups"
    )

    @property
    def get_all_members(self):
        from b3desk.models.users import User

        return (
            db.select(User)
            .join(group_member_table, User.id == group_member_table.c.user_id)
            .where(group_member_table.c.group_id == self.id)
            .order_by(User.family_name, User.given_name)
        )

    @property
    def get_all_exclude_users(self):
        from b3desk.models.users import User

        return (
            db.select(User)
            .join(excludelist_table, User.id == excludelist_table.c.user_id)
            .where(excludelist_table.c.group_id == self.id)
            .order_by(User.family_name, User.given_name)
        )
