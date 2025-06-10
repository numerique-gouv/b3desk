"""Adds sip-code in meeting.

Revision ID: 0052f608f4b3
Revises: 2e95af7b75cf
Create Date: 2025-06-10 12:41:24.218186
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from sqlalchemy.sql import update

from b3desk.models.meetings import unique_sip_code_generation

# revision identifiers, used by Alembic.
revision = "0052f608f4b3"
down_revision = "2e95af7b75cf"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(sa.Column("sip_code", sa.String(), nullable=True))
    bind = op.get_bind()
    session = Session(bind)
    meeting = sa.table(
        "meeting", sa.column("id", sa.Integer), sa.column("sip_code", sa.String)
    )
    generated_sip_code = []
    for (meeting_id,) in session.execute(select(meeting.c.id)):
        sip_code = unique_sip_code_generation(forbidden_sip_code=generated_sip_code)
        generated_sip_code.append(sip_code)
        session.execute(
            update(meeting).where(meeting.c.id == meeting_id).values(sip_code=sip_code)
        )
    session.commit()
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("sip_code", nullable=False)
        batch_op.create_unique_constraint("uq_meeting_sip_code", ["sip_code"])


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("sip_code")
