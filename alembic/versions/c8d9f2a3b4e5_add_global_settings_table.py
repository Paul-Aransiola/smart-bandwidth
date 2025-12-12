"""Add global_settings table

Revision ID: c8d9f2a3b4e5
Revises: bf45cc9a1e3f
Create Date: 2025-12-04 21:30:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Text, DateTime
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = "c8d9f2a3b4e5"
down_revision = "bf45cc9a1e3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add global_settings table for system-wide configuration."""
    op.create_table(
        "global_settings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "setting_key",
            String(255),
            nullable=False,
            unique=True,
            index=True,
            comment="Unique key for the setting",
        ),
        sa.Column(
            "setting_value",
            Text,
            nullable=True,
            comment="Value stored as text",
        ),
        sa.Column(
            "setting_type",
            String(50),
            nullable=False,
            comment="Type of the value: string, integer, float, boolean, json",
        ),
        sa.Column(
            "description",
            Text,
            nullable=True,
            comment="Human-readable description of the setting",
        ),
        sa.Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            comment="When the setting was created",
        ),
        sa.Column(
            "updated_at",
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
            comment="When the setting was last updated",
        ),
    )


def downgrade() -> None:
    """Remove global_settings table."""
    op.drop_table("global_settings")
