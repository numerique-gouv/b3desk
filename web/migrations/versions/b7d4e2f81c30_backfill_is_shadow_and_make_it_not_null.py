"""backfill is_shadow and make it non nullable.

2e95af7b75cf added is_shadow as nullable with neither a server default nor a
backfill, so every meeting that already existed then kept a NULL. Such a row
satisfies neither ``is_shadow IS TRUE`` nor ``is_shadow IS FALSE``, which
silently excludes it from the whole meeting lifecycle. A meeting is either a
shadow one or a regular one, so the third state is backfilled to false and
removed from the schema. The downgrade only restores the nullability: the
NULLs themselves carried no information worth restoring.

Revision ID: b7d4e2f81c30
Revises: c1f9c8e6a3d2
Create Date: 2026-09-15 11:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7d4e2f81c30"
down_revision = "c1f9c8e6a3d2"
branch_labels = None
depends_on = None

meeting_table = sa.table("meeting", sa.column("is_shadow", sa.Boolean()))


def upgrade():
    op.execute(
        meeting_table.update()
        .where(meeting_table.c.is_shadow.is_(None))
        .values(is_shadow=False)
    )

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("is_shadow", existing_type=sa.Boolean(), nullable=False)


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("is_shadow", existing_type=sa.Boolean(), nullable=True)
