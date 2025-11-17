"""
Schemas for reporting and analytics.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TimeSeriesDataPoint(BaseModel):
    """Single data point in a time series."""

    period: datetime = Field(..., description="Time period for this data point")
    total_bytes_sent: int = Field(..., ge=0, description="Total bytes sent in period")
    total_bytes_received: int = Field(..., ge=0, description="Total bytes received in period")
    total_bytes: int = Field(..., ge=0, description="Total bytes transferred in period")
    avg_upload_speed_mbps: float = Field(..., ge=0.0, description="Average upload speed in Mbps")
    avg_download_speed_mbps: float = Field(..., ge=0.0, description="Average download speed in Mbps")
    record_count: int = Field(..., ge=0, description="Number of records in period")


class BandwidthTrend(BaseModel):
    """Bandwidth usage trend over time."""

    device_id: int | None = Field(None, description="Device ID (None for all devices)")
    device_ip: str | None = Field(None, description="Device IP address")
    device_name: str | None = Field(None, description="Device name")
    start_date: datetime = Field(..., description="Start of trend period")
    end_date: datetime = Field(..., description="End of trend period")
    interval: Literal["hour", "day", "week"] = Field(..., description="Aggregation interval")
    data_points: list[TimeSeriesDataPoint] = Field(..., description="Time series data")
    total_bytes_sent: int = Field(..., ge=0, description="Total bytes sent in entire period")
    total_bytes_received: int = Field(..., ge=0, description="Total bytes received in entire period")
    total_bytes: int = Field(..., ge=0, description="Total bytes transferred in entire period")


class TopConsumer(BaseModel):
    """Top bandwidth consumer information."""

    device_id: int = Field(..., description="Device ID")
    device_ip: str = Field(..., description="Device IP address")
    device_name: str = Field(..., description="Device name")
    device_status: str = Field(..., description="Device status")
    total_bytes_sent: int = Field(..., ge=0, description="Total bytes sent")
    total_bytes_received: int = Field(..., ge=0, description="Total bytes received")
    total_bytes: int = Field(..., ge=0, description="Total bytes transferred")
    avg_upload_speed_mbps: float = Field(..., ge=0.0, description="Average upload speed in Mbps")
    avg_download_speed_mbps: float = Field(..., ge=0.0, description="Average download speed in Mbps")
    percentage_of_total: float = Field(..., ge=0.0, le=100.0, description="Percentage of total bandwidth")


class UsageReport(BaseModel):
    """Comprehensive bandwidth usage report."""

    report_type: Literal["device", "network"] = Field(..., description="Type of report")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")
    
    # Network-wide statistics
    total_devices: int = Field(..., ge=0, description="Total number of devices")
    active_devices: int = Field(..., ge=0, description="Number of active devices")
    total_bytes_sent: int = Field(..., ge=0, description="Total bytes sent by all devices")
    total_bytes_received: int = Field(..., ge=0, description="Total bytes received by all devices")
    total_bytes: int = Field(..., ge=0, description="Total bytes transferred")
    
    # Top consumers
    top_consumers: list[TopConsumer] = Field(default_factory=list, description="Top bandwidth consumers")
    
    # Device-specific data (if applicable)
    device_id: int | None = Field(None, description="Device ID for device-specific report")
    device_ip: str | None = Field(None, description="Device IP address")
    device_name: str | None = Field(None, description="Device name")


class ReportExportRequest(BaseModel):
    """Request parameters for report export."""

    report_type: Literal["usage", "trends", "top_consumers"] = Field(
        ..., description="Type of report to export"
    )
    format: Literal["csv", "json"] = Field(..., description="Export format")
    start_date: datetime = Field(..., description="Start date for report")
    end_date: datetime = Field(..., description="End date for report")
    device_id: int | None = Field(None, description="Optional device ID to filter by")
    interval: Literal["hour", "day", "week"] | None = Field(
        None, description="Interval for trends report"
    )
    limit: int | None = Field(None, ge=1, le=100, description="Limit for top consumers report")


class ReportExportResponse(BaseModel):
    """Response for report export."""

    filename: str = Field(..., description="Generated filename")
    format: Literal["csv", "json"] = Field(..., description="File format")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    record_count: int = Field(..., ge=0, description="Number of records in export")
    generated_at: datetime = Field(default_factory=datetime.now, description="Export generation time")
    download_url: str = Field(..., description="URL to download the export")
