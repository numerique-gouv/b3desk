"""VoiceBridge managed by b3desk.

Revision ID: c25342fd2428
Revises: 44cab47dbc9b
Create Date: 2025-03-25 08:23:29.169319
"""

import sqlalchemy as sa
from alembic import op
from b3desk.models.meetings import pin_generation
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from sqlalchemy.sql import update

# revision identifiers, used by Alembic.
revision = "c25342fd2428"
down_revision = "44cab47dbc9b"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind)
    meeting = sa.table(
        "meeting", sa.column("id", sa.Integer), sa.column("voiceBridge", sa.String)
    )
    generated_pins = []
    for (meeting_id,) in session.execute(select(meeting.c.id)):
        pin = pin_generation(forbidden_pins=generated_pins, clean_db=False)
        generated_pins.append(pin)
        session.execute(
            update(meeting).where(meeting.c.id == meeting_id).values(voiceBridge=pin)
        )
    session.commit()
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("voiceBridge", nullable=False)
        batch_op.create_unique_constraint("uq_meeting_voicebridge", ["voiceBridge"])
    op.create_table(
        "previous_voice_bridge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("voiceBridge", sa.Unicode(length=50), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voiceBridge"),
    )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_constraint("uq_meeting_voicebridge", type_="unique")
        batch_op.alter_column("voiceBridge", nullable=True)
    bind = op.get_bind()
    session = Session(bind)
    meeting = sa.table("meeting", sa.column("voiceBridge", sa.String))
    session.execute(update(meeting).values(voiceBridge=None))
    session.commit()
    op.drop_table("previous_voice_bridge")
