"""add unique constraint to trust_scores

Revision ID: 623a92c55973
Revises: 01f0599ab85f
Create Date: 2026-05-11 10:57:18.427763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '623a92c55973'
down_revision: Union[str, Sequence[str], None] = '01f0599ab85f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    from alembic import op
    import sqlalchemy as sa

    with op.batch_alter_table("trust_scores") as batch_op:
        batch_op.create_unique_constraint(
            "uq_trust_pair",
            ["user_a_id", "user_b_id"]
        )


def downgrade():
    from alembic import op

    with op.batch_alter_table("trust_scores") as batch_op:
        batch_op.drop_constraint("uq_trust_pair", type_="unique")
