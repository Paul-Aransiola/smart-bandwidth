"""
Schemas for advanced bandwidth control features.
"""

from datetime import datetime, time

from pydantic import BaseModel, Field, field_validator

from src.models.advanced_controls import QoSPriority, ScheduleRecurrence


# Bandwidth Quota schemas
class BandwidthQuotaBase(BaseModel):
    """Base schema for bandwidth quotas."""

    quota_name: str = Field(..., min_length=1, max_length=255, description="Quota name")
    quota_type: str = Field(..., description="Quota type: daily, weekly, monthly")
    limit_bytes: int = Field(..., gt=0, description="Quota limit in bytes")
    warning_threshold_percent: int = Field(
        80, ge=0, le=100, description="Warning threshold percentage"
    )
    device_id: int | None = Field(None, description="Device ID (None for global quota)")
    reset_day: int | None = Field(None, description="Day of month/week for reset (1-31 or 0-6)")

    @field_validator("quota_type")
    @classmethod
    def validate_quota_type(cls, v: str) -> str:
        """Validate quota type."""
        valid_types = {"daily", "weekly", "monthly"}
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid quota type. Must be one of: {valid_types}")
        return v.lower()


class BandwidthQuotaCreate(BandwidthQuotaBase):
    """Schema for creating a bandwidth quota."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "quota_name": "Monthly Data Cap",
                    "quota_type": "monthly",
                    "limit_bytes": 107374182400,  # 100 GB
                    "warning_threshold_percent": 80,
                    "device_id": 1,
                    "reset_day": 1,
                }
            ]
        }
    }


class BandwidthQuotaUpdate(BaseModel):
    """Schema for updating a bandwidth quota."""

    quota_name: str | None = None
    limit_bytes: int | None = Field(None, gt=0)
    warning_threshold_percent: int | None = Field(None, ge=0, le=100)
    is_active: bool | None = None


class BandwidthQuotaResponse(BandwidthQuotaBase):
    """Schema for bandwidth quota response."""

    id: int
    used_bytes: int
    is_active: bool
    usage_percent: float
    remaining_bytes: int
    last_reset_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# QoS Policy schemas
class QoSPolicyBase(BaseModel):
    """Base schema for QoS policies."""

    policy_name: str = Field(..., min_length=1, max_length=255, description="Policy name")
    description: str | None = Field(None, description="Policy description")
    priority: QoSPriority = Field(..., description="Traffic priority level")
    device_id: int | None = Field(None, description="Device ID (None for all traffic)")
    source_ip: str | None = Field(None, description="Source IP filter")
    destination_ip: str | None = Field(None, description="Destination IP filter")
    source_port: int | None = Field(None, ge=0, le=65535, description="Source port filter")
    destination_port: int | None = Field(None, ge=0, le=65535, description="Destination port filter")
    protocol: str | None = Field(None, description="Protocol filter (tcp, udp, icmp)")
    min_bandwidth_mbps: float | None = Field(None, ge=0, description="Minimum bandwidth guarantee")
    max_bandwidth_mbps: float | None = Field(None, ge=0, description="Maximum bandwidth limit")
    guaranteed_bandwidth_mbps: float | None = Field(
        None, ge=0, description="Guaranteed bandwidth allocation"
    )


class QoSPolicyCreate(QoSPolicyBase):
    """Schema for creating a QoS policy."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "policy_name": "VoIP Priority",
                    "description": "High priority for voice calls",
                    "priority": "critical",
                    "destination_port": 5060,
                    "protocol": "udp",
                    "guaranteed_bandwidth_mbps": 2.0,
                }
            ]
        }
    }


class QoSPolicyUpdate(BaseModel):
    """Schema for updating a QoS policy."""

    description: str | None = None
    priority: QoSPriority | None = None
    min_bandwidth_mbps: float | None = Field(None, ge=0)
    max_bandwidth_mbps: float | None = Field(None, ge=0)
    guaranteed_bandwidth_mbps: float | None = Field(None, ge=0)
    is_enabled: bool | None = None


class QoSPolicyResponse(QoSPolicyBase):
    """Schema for QoS policy response."""

    id: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Throttle Schedule schemas
class ThrottleScheduleBase(BaseModel):
    """Base schema for throttle schedules."""

    schedule_name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    description: str | None = Field(None, description="Schedule description")
    device_id: int | None = Field(None, description="Device ID (None for all devices)")
    throttle_limit_mbps: float = Field(..., gt=0, description="Throttle limit in Mbps")
    start_time: time = Field(..., description="Start time (HH:MM:SS)")
    end_time: time = Field(..., description="End time (HH:MM:SS)")
    recurrence: ScheduleRecurrence = Field(..., description="Schedule recurrence")
    days_of_week: str | None = Field(
        None, description="Days of week (0-6, comma-separated for weekly)"
    )
    start_date: datetime | None = Field(None, description="Schedule start date")
    end_date: datetime | None = Field(None, description="Schedule end date")


class ThrottleScheduleCreate(ThrottleScheduleBase):
    """Schema for creating a throttle schedule."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "schedule_name": "Peak Hours Throttle",
                    "description": "Reduce bandwidth during peak usage hours",
                    "throttle_limit_mbps": 10.0,
                    "start_time": "18:00:00",
                    "end_time": "23:00:00",
                    "recurrence": "daily",
                    "days_of_week": "0,1,2,3,4",
                }
            ]
        }
    }


class ThrottleScheduleUpdate(BaseModel):
    """Schema for updating a throttle schedule."""

    description: str | None = None
    throttle_limit_mbps: float | None = Field(None, gt=0)
    start_time: time | None = None
    end_time: time | None = None
    is_enabled: bool | None = None


class ThrottleScheduleResponse(ThrottleScheduleBase):
    """Schema for throttle schedule response."""

    id: int
    is_enabled: bool
    last_executed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Quota usage statistics
class QuotaUsageStats(BaseModel):
    """Quota usage statistics."""

    device_id: int | None
    device_name: str | None
    total_quotas: int
    active_quotas: int
    total_limit_bytes: int
    total_used_bytes: int
    overall_usage_percent: float
    quotas_near_limit: int  # Number of quotas above warning threshold
