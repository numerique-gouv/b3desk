"""Adds visio-code in meeting.

Revision ID: 0052f608f4b3
Revises: 2e95af7b75cf
Create Date: 2025-06-10 12:41:24.218186
"""

import random

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from sqlalchemy.sql import update

# revision identifiers, used by Alembic.
revision = "0052f608f4b3"
down_revision = "2e95af7b75cf"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(sa.Column("visio_code", sa.String(), nullable=True))
    bind = op.get_bind()
    session = Session(bind)
    meeting = sa.table(
        "meeting", sa.column("id", sa.Integer), sa.column("visio_code", sa.String)
    )
    count = session.execute(select(sa.func.count()).select_from(meeting)).scalar()
    codes = iter(str(c) for c in random.sample(range(100000000, 1000000000), count))
    for (meeting_id,) in session.execute(select(meeting.c.id)):
        session.execute(
            update(meeting)
            .where(meeting.c.id == meeting_id)
            .values(visio_code=next(codes))
        )
    session.commit()
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("visio_code", nullable=False)
        batch_op.create_unique_constraint("uq_meeting_visio_code", ["visio_code"])


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("visio_code")
