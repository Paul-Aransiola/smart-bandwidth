"""add_performance_indexes

Revision ID: 078ebbc869a3
Revises: 954cfe4222a0
Create Date: 2025-11-18 17:04:10.389650

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "078ebbc869a3"
down_revision: Union[str, Sequence[str], None] = "954cfe4222a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    # Devices table indexes
    op.create_index("idx_devices_ip_address", "devices", ["ip_address"], unique=False)
    op.create_index("idx_devices_mac_address", "devices", ["mac_address"], unique=False)
    op.create_index("idx_devices_status", "devices", ["status"], unique=False)

    # Bandwidth usage indexes
    op.create_index(
        "idx_bandwidth_device_timestamp",
        "bandwidth_usage",
        ["device_id", "timestamp"],
        unique=False,
    )
    op.create_index("idx_bandwidth_timestamp", "bandwidth_usage", ["timestamp"], unique=False)

    # Alert rules indexes
    op.create_index("idx_alert_rules_device", "alert_rules", ["device_id"], unique=False)
    op.create_index("idx_alert_rules_enabled", "alert_rules", ["is_enabled"], unique=False)

    # Alerts indexes
    op.create_index(
        "idx_alerts_device_triggered", "alerts", ["device_id", "triggered_at"], unique=False
    )
    op.create_index("idx_alerts_status", "alerts", ["status"], unique=False)
    op.create_index("idx_alerts_triggered_at", "alerts", ["triggered_at"], unique=False)

    # Advanced controls indexes (bandwidth quotas)
    op.create_index("idx_bandwidth_quotas_device", "bandwidth_quotas", ["device_id"], unique=False)
    op.create_index("idx_bandwidth_quotas_active", "bandwidth_quotas", ["is_active"], unique=False)

    # QoS policies indexes
    op.create_index("idx_qos_policies_device", "qos_policies", ["device_id"], unique=False)
    op.create_index("idx_qos_policies_active", "qos_policies", ["is_active"], unique=False)

    # Throttle schedules indexes
    op.create_index(
        "idx_throttle_schedules_device", "throttle_schedules", ["device_id"], unique=False
    )
    op.create_index(
        "idx_throttle_schedules_active", "throttle_schedules", ["is_active"], unique=False
    )


def downgrade() -> None:
    """Remove performance indexes."""
    # Drop indexes in reverse order
    op.drop_index("idx_throttle_schedules_active", table_name="throttle_schedules")
    op.drop_index("idx_throttle_schedules_device", table_name="throttle_schedules")
    op.drop_index("idx_qos_policies_active", table_name="qos_policies")
    op.drop_index("idx_qos_policies_device", table_name="qos_policies")
    op.drop_index("idx_bandwidth_quotas_active", table_name="bandwidth_quotas")
    op.drop_index("idx_bandwidth_quotas_device", table_name="bandwidth_quotas")
    op.drop_index("idx_alerts_triggered_at", table_name="alerts")
    op.drop_index("idx_alerts_status", table_name="alerts")
    op.drop_index("idx_alerts_device_triggered", table_name="alerts")
    op.drop_index("idx_alert_rules_enabled", table_name="alert_rules")
    op.drop_index("idx_alert_rules_device", table_name="alert_rules")
    op.drop_index("idx_bandwidth_timestamp", table_name="bandwidth_usage")
    op.drop_index("idx_bandwidth_device_timestamp", table_name="bandwidth_usage")
    op.drop_index("idx_devices_status", table_name="devices")
    op.drop_index("idx_devices_mac_address", table_name="devices")
    op.drop_index("idx_devices_ip_address", table_name="devices")
