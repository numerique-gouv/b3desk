from enum import IntEnum

from . import db


class PermissionLevel(IntEnum):
    No_PERMISSION = 0
    DELEGATE = 1


class Permission(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("meeting.id"), primary_key=True)
    permission = db.Column(db.Enum(PermissionLevel), nullable=False)

    user = db.relationship("User", backref="user_permission")
    meeting = db.relationship("Meeting", backref="meeting_permission")

    def save(self):
        """Save the permission to the database."""
        db.session.add(self)
        db.session.commit()


def get_permission(user_id, meeting_id):
    permission = Permission.query.filter_by(
        user_id=user_id, meeting_id=meeting_id
    ).one_or_none()
    return permission


favorite_table = db.Table(
    "favorite",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("meeting_id", db.Integer, db.ForeignKey("meeting.id"), primary_key=True),
)
