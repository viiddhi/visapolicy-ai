"""initial schema

Revision ID: 001
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_documents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("doc_number", sa.String(32), nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("body_url", sa.Text),
        sa.Column("published_at", sa.Date, nullable=False),
        sa.Column("effective_at", sa.Date),
        sa.Column("rule_type", sa.String(32)),
        sa.Column("overall_impact_level", sa.String(16)),
        sa.Column("raw_text", sa.Text),
        sa.Column("processed", sa.Boolean, default=False),
        sa.Column("fetched_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "rule_changes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("document_id", sa.String(64), sa.ForeignKey("policy_documents.id"), nullable=False),
        sa.Column("section", sa.Text),
        sa.Column("topic", sa.Text, nullable=False),
        sa.Column("old_rule", sa.Text, nullable=False),
        sa.Column("new_rule", sa.Text, nullable=False),
        sa.Column("plain_english_summary", sa.Text, nullable=False),
        sa.Column("impact_level", sa.String(16), nullable=False),
        sa.Column("action_required", sa.Boolean, default=False),
        sa.Column("action_description", sa.Text),
        sa.Column("visa_categories_affected", sa.JSON),
        sa.Column("who_is_affected", sa.JSON),
        sa.Column("tags", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255)),
        sa.Column("visa_categories", sa.JSON),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "alert_logs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rule_change_id", sa.String(64), sa.ForeignKey("rule_changes.id"), nullable=False),
        sa.Column("alert_type", sa.String(32), default="email"),
        sa.Column("status", sa.String(32), default="pending"),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("ix_rule_changes_document_id", "rule_changes", ["document_id"])
    op.create_index("ix_rule_changes_impact_level", "rule_changes", ["impact_level"])
    op.create_index("ix_alert_logs_user_id", "alert_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("alert_logs")
    op.drop_table("users")
    op.drop_table("rule_changes")
    op.drop_table("policy_documents")
