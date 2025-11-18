"""add_performance_indexes

Revision ID: 954cfe4222a0
Revises: 634a0e21f219
Create Date: 2025-11-18 11:08:58.298056

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "954cfe4222a0"
down_revision: Union[str, Sequence[str], None] = "634a0e21f219"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add performance indexes."""
    # Devices table indexes
    op.create_index("idx_devices_ip_address", "devices", ["ip_address"], unique=False)
    op.create_index("idx_devices_mac_address", "devices", ["mac_address"], unique=False)
    op.create_index("idx_devices_status", "devices", ["status"], unique=False)
    op.create_index("idx_devices_is_blocked", "devices", ["is_blocked"], unique=False)
    op.create_index("idx_devices_is_throttled", "devices", ["is_throttled"], unique=False)
    op.create_index("idx_devices_last_seen", "devices", ["last_seen"], unique=False)

    # Bandwidth usage indexes
    op.create_index("idx_bandwidth_usage_device_id", "bandwidth_usage", ["device_id"], unique=False)
    op.create_index("idx_bandwidth_usage_timestamp", "bandwidth_usage", ["timestamp"], unique=False)
    op.create_index(
        "idx_bandwidth_usage_device_timestamp",
        "bandwidth_usage",
        ["device_id", "timestamp"],
        unique=False,
    )

    # Alert rules indexes
    op.create_index("idx_alert_rules_device_id", "alert_rules", ["device_id"], unique=False)
    op.create_index("idx_alert_rules_is_enabled", "alert_rules", ["is_enabled"], unique=False)

    # Alerts indexes
    op.create_index("idx_alerts_device_id", "alerts", ["device_id"], unique=False)
    op.create_index("idx_alerts_status", "alerts", ["status"], unique=False)
    op.create_index("idx_alerts_triggered_at", "alerts", ["triggered_at"], unique=False)

    # Note: bandwidth_quotas and throttle_schedules indexes will be added
    # when those tables are created in Feature 6 migration


def downgrade() -> None:
    """Downgrade schema - Remove performance indexes."""
    # Alerts indexes
    op.drop_index("idx_alerts_triggered_at", table_name="alerts")
    op.drop_index("idx_alerts_status", table_name="alerts")
    op.drop_index("idx_alerts_device_id", table_name="alerts")

    # Alert rules indexes
    op.drop_index("idx_alert_rules_is_enabled", table_name="alert_rules")
    op.drop_index("idx_alert_rules_device_id", table_name="alert_rules")

    # Bandwidth usage indexes
    op.drop_index("idx_bandwidth_usage_device_timestamp", table_name="bandwidth_usage")
    op.drop_index("idx_bandwidth_usage_timestamp", table_name="bandwidth_usage")
    op.drop_index("idx_bandwidth_usage_device_id", table_name="bandwidth_usage")

    # Devices table indexes
    op.drop_index("idx_devices_last_seen", table_name="devices")
    op.drop_index("idx_devices_is_throttled", table_name="devices")
    op.drop_index("idx_devices_is_blocked", table_name="devices")
    op.drop_index("idx_devices_status", table_name="devices")
    op.drop_index("idx_devices_mac_address", table_name="devices")
    op.drop_index("idx_devices_ip_address", table_name="devices")
