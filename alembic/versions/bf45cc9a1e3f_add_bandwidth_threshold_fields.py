"""Add bandwidth threshold fields to devices

Revision ID: bf45cc9a1e3f
Revises: 078ebbc869a3
Create Date: 2025-12-04 20:50:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, Float, Integer


# revision identifiers, used by Alembic.
revision = "bf45cc9a1e3f"
down_revision = "078ebbc869a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add bandwidth threshold monitoring fields to devices table."""
    # Add bandwidth_threshold_mbps column
    op.add_column(
        "devices",
        sa.Column(
            "bandwidth_threshold_mbps",
            Float,
            nullable=True,
            comment="Bandwidth threshold in Mbps - triggers alert/deactivation",
        ),
    )

    # Add auto_deactivate_on_threshold column
    op.add_column(
        "devices",
        sa.Column(
            "auto_deactivate_on_threshold",
            Boolean,
            nullable=False,
            server_default="0",
            comment="Auto-deactivate when threshold exceeded",
        ),
    )

    # Add threshold_time_window_minutes column
    op.add_column(
        "devices",
        sa.Column(
            "threshold_time_window_minutes",
            Integer,
            nullable=False,
            server_default="5",
            comment="Time window for threshold evaluation in minutes",
        ),
    )

    # Add threshold_breach_count column
    op.add_column(
        "devices",
        sa.Column(
            "threshold_breach_count",
            Integer,
            nullable=False,
            server_default="0",
            comment="Number of times threshold has been breached",
        ),
    )

    # Add last_threshold_breach column
    op.add_column(
        "devices",
        sa.Column(
            "last_threshold_breach",
            DateTime(timezone=True),
            nullable=True,
            comment="Last time threshold was breached",
        ),
    )


def downgrade() -> None:
    """Remove bandwidth threshold fields from devices table."""
    op.drop_column("devices", "last_threshold_breach")
    op.drop_column("devices", "threshold_breach_count")
    op.drop_column("devices", "threshold_time_window_minutes")
    op.drop_column("devices", "auto_deactivate_on_threshold")
    op.drop_column("devices", "bandwidth_threshold_mbps")
