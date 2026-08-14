from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Unicode
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from . import db

if TYPE_CHECKING:
    from .users import User

group_member_table = db.Table(
    "group_member",
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("group_id", ForeignKey("group.id"), primary_key=True),
)


class Group(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    name: Mapped[str | None] = mapped_column(Unicode(150), unique=True)
    enable_sip: Mapped[bool | None] = mapped_column(default=None)
    enable_file_sharing: Mapped[bool | None] = mapped_column(default=None)
    enable_ai_summary: Mapped[bool | None] = mapped_column(default=None)

    members: Mapped[list[User]] = relationship(
        secondary=group_member_table, back_populates="groups"
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
