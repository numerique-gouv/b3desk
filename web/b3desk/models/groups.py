from datetime import datetime

from . import db

group_member_table = db.Table(
    "group_member",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("group.id"), primary_key=True),
)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    name = db.Column(db.Unicode(150), unique=True)
    enable_sip = db.Column(db.Boolean, default=None)
    enable_file_sharing = db.Column(db.Boolean, default=None)
    enable_transcription = db.Column(db.Boolean, default=None)

    members = db.relationship(
        "User", secondary=group_member_table, back_populates="groups"
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
