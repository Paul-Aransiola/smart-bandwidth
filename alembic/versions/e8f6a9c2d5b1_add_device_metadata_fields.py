"""Add device metadata fields (device_type, manufacturer, os_type)

Revision ID: e8f6a9c2d5b1
Revises: c8d9f2a3b4e5
Create Date: 2025-12-05 12:45:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String


# revision identifiers, used by Alembic.
revision = "e8f6a9c2d5b1"
down_revision = "c8d9f2a3b4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add device metadata fields to devices table."""
    # Add device_type column
    op.add_column(
        "devices",
        sa.Column(
            "device_type",
            String(50),
            nullable=True,
            comment="Device type (mobile, computer, router, etc.)",
        ),
    )

    # Add manufacturer column
    op.add_column(
        "devices",
        sa.Column(
            "manufacturer",
            String(255),
            nullable=True,
            comment="Device manufacturer from MAC address",
        ),
    )

    # Add os_type column
    op.add_column(
        "devices",
        sa.Column(
            "os_type",
            String(100),
            nullable=True,
            comment="Operating system type",
        ),
    )


def downgrade() -> None:
    """Remove device metadata fields from devices table."""
    op.drop_column("devices", "os_type")
    op.drop_column("devices", "manufacturer")
    op.drop_column("devices", "device_type")
