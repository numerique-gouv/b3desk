"""creates delegate table for meeting delegation.

Revision ID: d01b2eda957f
Revises: f68adee062bf
Create Date: 2025-11-12 14:04:20.242269

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.sql import insert
from sqlalchemy.sql import select
from sqlalchemy.sql import update

# revision identifiers, used by Alembic.
revision = "d01b2eda957f"
down_revision = "f68adee062bf"
branch_labels = None
depends_on = None


def upgrade():
    # create new table : delegate
    op.create_table(
        "delegate",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meeting.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "meeting_id"),
    )
    # create new table : favorite
    op.create_table(
        "favorite",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meeting.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "meeting_id"),
    )
    # save previous favorites in favorite table
    bind = op.get_bind()
    session = Session(bind)
    favorites = sa.table(
        "favorite",
        sa.column("meeting_id", sa.Integer),
        sa.column("user_id", sa.Integer),
    )
    meetings = sa.table(
        "meeting",
        sa.column("id", sa.Integer),
        sa.column("user_id", sa.Integer),
        sa.column("is_favorite", sa.Boolean),
    )

    favorite_meetings = select(meetings).where(meetings.c.is_favorite)

    for (
        meeting_id,
        user_id,
    ) in session.execute(select(favorite_meetings.c.id, favorite_meetings.c.user_id)):
        session.execute(
            insert(favorites).values(user_id=user_id, meeting_id=meeting_id)
        )
    session.commit()

    # delete is_favorite column in meeting table
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("is_favorite")


def downgrade():
    # create is_favorite column in meeting table
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_favorite", sa.BOOLEAN(), autoincrement=False, nullable=True)
        )

    # save previous favorites in meeting table
    bind = op.get_bind()
    session = Session(bind)
    meetings = sa.table(
        "meeting",
        sa.column("id", sa.Integer),
        sa.column("user_id", sa.Integer),
        sa.column("is_favorite", sa.Boolean),
    )
    favorites = sa.table(
        "favorite",
        sa.column("meeting_id", sa.Integer),
        sa.column("user_id", sa.Integer),
    )
    for (
        meeting_id,
        user_id,
    ) in session.execute(select(favorites.c.meeting_id, favorites.c.user_id)):
        session.execute(
            update(meetings)
            .where(meetings.c.id == meeting_id)
            .where(meetings.c.user_id == user_id)
            .values(is_favorite=True)
        )
    session.commit()

    # delete favorite and delegate tables
    op.drop_table("favorite")
    op.drop_table("delegate")
