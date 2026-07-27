"""add password reset token fields

Revision ID: 003
Revises: 002
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("reset_token", sa.String(128), unique=True))
    op.add_column("users", sa.Column("reset_token_expires", sa.DateTime))


def downgrade() -> None:
    op.drop_column("users", "reset_token")
    op.drop_column("users", "reset_token_expires")
