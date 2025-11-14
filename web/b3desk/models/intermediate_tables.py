from . import db

delegate_table = db.Table(
    "delegate",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("meeting_id", db.Integer, db.ForeignKey("meeting.id"), primary_key=True),
)

favorite_table = db.Table(
    "favorite",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("meeting_id", db.Integer, db.ForeignKey("meeting.id"), primary_key=True),
)
