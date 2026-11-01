"""add course level

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29 22:39:11.803203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('courses', sa.Column('level', sa.Text(), nullable=True))
    op.execute(
        "UPDATE courses SET level = CASE WHEN is_elective "
        "THEN 'beginner' ELSE 'intermediate' END"
    )
    op.alter_column('courses', 'level', existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('courses', 'level')
