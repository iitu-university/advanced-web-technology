"""Create users linked to student profiles."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), server_default=sa.text("'student'"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("role IN ('student', 'admin')", name=op.f("users_role_check")),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("users_student_id_fkey"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("users_pkey")),
        sa.UniqueConstraint("email", name=op.f("users_email_key")),
        sa.UniqueConstraint("student_id", name=op.f("users_student_id_key")),
    )


def downgrade() -> None:
    op.drop_table("users")
