"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeviceStatus(str, Enum):
    """Device status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    THROTTLED = "throttled"
    DEACTIVATED = "deactivated"


# Base schemas
class DeviceBase(BaseModel):
    """Base schema for device."""

    ip_address: str = Field(..., description="Device IP address", examples=["192.168.1.100"])
    mac_address: str = Field(..., description="Device MAC address", examples=["00:11:22:33:44:55"])
    hostname: str | None = Field(None, description="Device hostname", examples=["johns-laptop"])
    device_name: str | None = Field(
        None, description="Custom device name", examples=["John's Laptop"]
    )
    device_type: str | None = Field(
        None, description="Device type classification", examples=["mobile", "computer", "router"]
    )
    manufacturer: str | None = Field(
        None, description="Device manufacturer", examples=["Apple", "Samsung"]
    )
    os_type: str | None = Field(
        None, description="Operating system type", examples=["iOS", "Android", "Windows"]
    )
    notes: str | None = Field(None, description="Additional notes")

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validate and normalize MAC address format."""
        v = v.upper().replace("-", ":").replace(".", ":")
        parts = v.split(":")

        # Pad single-digit hex values with leading zero
        parts = [p.zfill(2) if len(p) == 1 else p for p in parts]

        if len(parts) != 6 or not all(
            len(p) == 2 and all(c in "0123456789ABCDEF" for c in p) for p in parts
        ):
            raise ValueError("Invalid MAC address format")
        return ":".join(parts)

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Basic IPv4 address validation."""
        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError("Invalid IP address format")
        try:
            if not all(0 <= int(part) <= 255 for part in parts):
                raise ValueError("Invalid IP address range")
        except ValueError as exc:
            raise ValueError("Invalid IP address format") from exc
        return v


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""

    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""

    hostname: str | None = None
    device_name: str | None = None
    notes: str | None = None
    status: DeviceStatus | None = None
    bandwidth_threshold_mbps: float | None = Field(
        None, ge=0, description="Bandwidth threshold in Mbps"
    )
    auto_deactivate_on_threshold: bool | None = Field(
        None, description="Auto-deactivate when threshold exceeded"
    )
    threshold_time_window_minutes: int | None = Field(
        None, ge=1, le=1440, description="Time window for threshold check (1-1440 minutes)"
    )


class DeviceResponse(DeviceBase):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: DeviceStatus
    first_seen: datetime
    last_seen: datetime
    is_blocked: bool
    is_throttled: bool
    throttle_limit_mbps: float | None
    bandwidth_threshold_mbps: float | None
    auto_deactivate_on_threshold: bool
    threshold_time_window_minutes: int
    threshold_breach_count: int
    last_threshold_breach: datetime | None
    total_bytes_sent: int
    total_bytes_received: int

    @property
    def total_bytes(self) -> int:
        """Calculate total bytes."""
        return self.total_bytes_sent + self.total_bytes_received


# Bandwidth Usage schemas
class BandwidthUsageBase(BaseModel):
    """Base schema for bandwidth usage."""

    bytes_sent: int = Field(ge=0, description="Bytes sent")
    bytes_received: int = Field(ge=0, description="Bytes received")
    packets_sent: int = Field(ge=0, description="Packets sent")
    packets_received: int = Field(ge=0, description="Packets received")
    upload_speed_mbps: float = Field(ge=0.0, description="Upload speed in Mbps")
    download_speed_mbps: float = Field(ge=0.0, description="Download speed in Mbps")


class BandwidthUsageCreate(BandwidthUsageBase):
    """Schema for creating bandwidth usage record."""

    device_id: int


class BandwidthUsageResponse(BandwidthUsageBase):
    """Schema for bandwidth usage response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    timestamp: datetime

    @property
    def total_bytes(self) -> int:
        """Calculate total bytes."""
        return self.bytes_sent + self.bytes_received


# Block History schemas
class BlockHistoryBase(BaseModel):
    """Base schema for block history."""

    action: str = Field(..., description="Action performed", examples=["block", "unblock"])
    reason: str | None = Field(None, description="Reason for action")
    throttle_limit_mbps: float | None = Field(None, ge=0, description="Throttle limit in Mbps")
    created_by: str | None = Field(None, description="User who performed action")


class BlockHistoryCreate(BlockHistoryBase):
    """Schema for creating block history record."""

    device_id: int


class BlockHistoryResponse(BlockHistoryBase):
    """Schema for block history response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    created_at: datetime


# Control operation schemas
class BlockDeviceRequest(BaseModel):
    """Schema for blocking a device."""

    reason: str | None = Field(None, description="Reason for blocking")


class ThrottleDeviceRequest(BaseModel):
    """Schema for throttling a device."""

    limit_mbps: float = Field(..., gt=0, description="Throttle limit in Mbps", examples=[10.0])
    reason: str | None = Field(None, description="Reason for throttling")


# Statistics schemas
class DeviceStatistics(BaseModel):
    """Schema for device statistics."""

    total_devices: int
    active_devices: int
    blocked_devices: int
    throttled_devices: int
    total_bandwidth_used: int


class BandwidthStatistics(BaseModel):
    """Schema for bandwidth statistics."""

    device_id: int
    ip_address: str
    mac_address: str
    total_bytes_sent: int
    total_bytes_received: int
    total_bytes: int
    avg_upload_speed_mbps: float
    avg_download_speed_mbps: float
    peak_upload_speed_mbps: float
    peak_download_speed_mbps: float
    first_recorded: datetime
    last_recorded: datetime


# Error response schema
class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(..., description="Error detail message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
