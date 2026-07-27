"""expand user profile

Revision ID: 002
Revises: 001
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255)))
    op.add_column("users", sa.Column("primary_visa_type", sa.String(32)))
    op.add_column("users", sa.Column("visa_status", sa.String(32)))
    op.add_column("users", sa.Column("authorized_until", sa.Date))
    op.add_column("users", sa.Column("gc_stage", sa.String(32)))
    op.add_column("users", sa.Column("priority_date", sa.Date))
    op.add_column("users", sa.Column("preference_category", sa.String(16)))
    op.add_column("users", sa.Column("country_of_birth", sa.String(64)))
    op.add_column("users", sa.Column("employer_type", sa.String(32)))
    op.add_column("users", sa.Column("placement_type", sa.String(32)))
    op.add_column("users", sa.Column("degree_field", sa.String(128)))
    op.add_column("users", sa.Column("job_title", sa.String(128)))
    op.add_column("users", sa.Column("on_opt", sa.Boolean, server_default="false"))
    op.add_column("users", sa.Column("opt_type", sa.String(16)))
    op.add_column("users", sa.Column("opt_expiry", sa.Date))
    op.add_column("users", sa.Column("dependent_visa_types", sa.JSON))
    op.add_column("users", sa.Column("alert_frequency", sa.String(16), server_default="daily"))
    op.add_column("users", sa.Column("min_impact_level", sa.String(16), server_default="medium"))
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean, server_default="false"))
    op.add_column("users", sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()))


def downgrade() -> None:
    for col in [
        "password_hash", "primary_visa_type", "visa_status", "authorized_until",
        "gc_stage", "priority_date", "preference_category", "country_of_birth",
        "employer_type", "placement_type", "degree_field", "job_title",
        "on_opt", "opt_type", "opt_expiry", "dependent_visa_types",
        "alert_frequency", "min_impact_level", "onboarding_completed", "updated_at",
    ]:
        op.drop_column("users", col)
