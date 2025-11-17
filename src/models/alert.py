"""
Database models for alert system.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class AlertSeverity(str, PyEnum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, PyEnum):
    """Alert lifecycle status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SNOOZED = "snoozed"


class AlertCondition(str, PyEnum):
    """Alert rule condition types."""

    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"


class AlertMetric(str, PyEnum):
    """Metrics that can trigger alerts."""

    BANDWIDTH_USAGE = "bandwidth_usage"
    UPLOAD_SPEED = "upload_speed"
    DOWNLOAD_SPEED = "download_speed"
    TOTAL_BYTES = "total_bytes"
    DEVICE_COUNT = "device_count"


class NotificationChannel(str, PyEnum):
    """Available notification channels."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"


class AlertRule(Base):
    """
    Alert rule defining when to trigger alerts.
    """

    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Rule configuration
    metric: Mapped[AlertMetric] = mapped_column(
        Enum(AlertMetric), nullable=False, index=True
    )
    condition: Mapped[AlertCondition] = mapped_column(
        Enum(AlertCondition), nullable=False
    )
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    time_window_minutes: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False,
        comment="Time window in minutes for evaluation"
    )
    
    # Targeting
    device_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Specific device to monitor (NULL for all devices)"
    )
    
    # Notification settings
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False
    )
    notification_channels: Mapped[str] = mapped_column(
        String(255),
        default="websocket",
        nullable=False,
        comment="Comma-separated list of channels: email,webhook,websocket"
    )
    notification_config: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON configuration for notifications (email addresses, webhook URLs)"
    )
    
    # Cooldown and rate limiting
    cooldown_minutes: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False,
        comment="Minutes to wait before triggering same alert again"
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Rule state
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    device: Mapped["Device"] = relationship(
        "Device", back_populates="alert_rules", lazy="selectin"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="rule", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_alert_rules_enabled_metric", "is_enabled", "metric"),
    )


class Alert(Base):
    """
    Alert instance representing a triggered alert.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    device_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Alert details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity), nullable=False, index=True
    )
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True
    )
    
    # Metric data at time of alert
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Timestamps
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    snoozed_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notification tracking
    notifications_sent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON array of notification delivery records"
    )
    
    # Relationships
    rule: Mapped[AlertRule] = relationship("AlertRule", back_populates="alerts", lazy="selectin")
    device: Mapped["Device"] = relationship("Device", back_populates="alerts", lazy="selectin")

    __table_args__ = (
        Index("idx_alerts_status_severity", "status", "severity"),
        Index("idx_alerts_triggered", "triggered_at"),
    )
