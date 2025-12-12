"""
Schemas for alert system.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.models.alert import AlertCondition, AlertMetric, AlertSeverity, AlertStatus


class NotificationConfig(BaseModel):
    """Notification configuration."""

    email_addresses: list[str] = Field(
        default_factory=list, description="Email addresses for notifications"
    )
    webhook_urls: list[str] = Field(
        default_factory=list, description="Webhook URLs for notifications"
    )
    email_template: str | None = Field(None, description="Custom email template")


class AlertRuleBase(BaseModel):
    """Base schema for alert rules."""

    name: str = Field(..., min_length=1, max_length=255, description="Rule name")
    description: str | None = Field(None, description="Rule description")
    metric: AlertMetric = Field(..., description="Metric to monitor")
    condition: AlertCondition = Field(..., description="Condition to evaluate")
    threshold_value: float = Field(..., description="Threshold value for the condition")
    time_window_minutes: int = Field(5, ge=1, le=1440, description="Time window in minutes")
    device_id: int | None = Field(None, description="Specific device ID (None for all devices)")
    severity: AlertSeverity = Field(AlertSeverity.WARNING, description="Alert severity")
    notification_channels: str = Field(
        "websocket", description="Comma-separated notification channels"
    )
    notification_config: NotificationConfig | None = Field(
        None, description="Notification configuration"
    )
    cooldown_minutes: int = Field(15, ge=1, le=1440, description="Cooldown period in minutes")
    is_enabled: bool = Field(True, description="Whether the rule is enabled")


class AlertRuleCreate(AlertRuleBase):
    """Schema for creating an alert rule."""

    @field_validator("notification_channels")
    @classmethod
    def validate_channels(cls, v: str) -> str:
        """Validate notification channels."""
        valid_channels = {"email", "webhook", "websocket"}
        channels = {ch.strip() for ch in v.split(",") if ch.strip()}
        invalid = channels - valid_channels
        if invalid:
            raise ValueError(f"Invalid channels: {invalid}. Valid: {valid_channels}")
        return ",".join(sorted(channels))


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    metric: AlertMetric | None = None
    condition: AlertCondition | None = None
    threshold_value: float | None = None
    time_window_minutes: int | None = Field(None, ge=1, le=1440)
    device_id: int | None = None
    severity: AlertSeverity | None = None
    notification_channels: str | None = None
    notification_config: NotificationConfig | None = None
    cooldown_minutes: int | None = Field(None, ge=1, le=1440)
    is_enabled: bool | None = None


class AlertRuleResponse(AlertRuleBase):
    """Schema for alert rule response."""

    id: int = Field(..., description="Rule ID")
    last_triggered_at: datetime | None = Field(None, description="Last time the rule was triggered")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @field_validator("notification_config", mode="before")
    @classmethod
    def parse_notification_config(cls, v):
        """Parse notification_config from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    """Base schema for alerts."""

    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    severity: AlertSeverity = Field(..., description="Alert severity")
    metric_value: float = Field(..., description="Actual metric value")
    threshold_value: float = Field(..., description="Threshold value that was exceeded")


class AlertResponse(AlertBase):
    """Schema for alert response."""

    id: int = Field(..., description="Alert ID")
    rule_id: int = Field(..., description="Associated rule ID")
    device_id: int | None = Field(None, description="Associated device ID")
    status: AlertStatus = Field(..., description="Alert status")
    triggered_at: datetime = Field(..., description="When the alert was triggered")
    acknowledged_at: datetime | None = Field(None, description="When the alert was acknowledged")
    resolved_at: datetime | None = Field(None, description="When the alert was resolved")
    snoozed_until: datetime | None = Field(None, description="Snoozed until timestamp")

    # Enriched data
    rule_name: str | None = Field(None, description="Rule name")
    device_ip: str | None = Field(None, description="Device IP address")
    device_name: str | None = Field(None, description="Device name")

    class Config:
        from_attributes = True


class AlertUpdateStatus(BaseModel):
    """Schema for updating alert status."""

    status: Literal["acknowledged", "resolved", "snoozed"] = Field(..., description="New status")
    snooze_minutes: int | None = Field(
        None, ge=1, le=1440, description="Minutes to snooze (if snoozed)"
    )


class AlertQuery(BaseModel):
    """Schema for querying alerts."""

    status: AlertStatus | None = Field(None, description="Filter by status")
    severity: AlertSeverity | None = Field(None, description="Filter by severity")
    device_id: int | None = Field(None, description="Filter by device")
    rule_id: int | None = Field(None, description="Filter by rule")
    start_date: datetime | None = Field(None, description="Filter by start date")
    end_date: datetime | None = Field(None, description="Filter by end date")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records")


class AlertStatistics(BaseModel):
    """Alert statistics."""

    total_alerts: int = Field(..., ge=0, description="Total number of alerts")
    active_alerts: int = Field(..., ge=0, description="Number of active alerts")
    acknowledged_alerts: int = Field(..., ge=0, description="Number of acknowledged alerts")
    resolved_alerts: int = Field(..., ge=0, description="Number of resolved alerts")
    critical_alerts: int = Field(..., ge=0, description="Number of critical alerts")
    by_severity: dict[str, int] = Field(default_factory=dict, description="Alerts by severity")
    by_status: dict[str, int] = Field(default_factory=dict, description="Alerts by status")
    by_rule: dict[str, int] = Field(default_factory=dict, description="Alerts by rule")
    recent_alerts: list[AlertResponse] = Field(default_factory=list, description="Recent alerts")


class NotificationDelivery(BaseModel):
    """Notification delivery record."""

    channel: str = Field(..., description="Notification channel")
    sent_at: datetime = Field(..., description="When notification was sent")
    success: bool = Field(..., description="Whether delivery was successful")
    error: str | None = Field(None, description="Error message if failed")
    recipient: str | None = Field(None, description="Recipient (email/webhook URL)")
