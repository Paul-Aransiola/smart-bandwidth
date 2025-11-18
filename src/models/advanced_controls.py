"""
Database models for advanced bandwidth control features.
"""

from datetime import datetime, time
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class QoSPriority(str, PyEnum):
    """Quality of Service priority levels."""

    CRITICAL = "critical"  # Highest priority (e.g., VoIP, video conferencing)
    HIGH = "high"  # High priority (e.g., streaming, gaming)
    MEDIUM = "medium"  # Normal priority (e.g., browsing)
    LOW = "low"  # Low priority (e.g., downloads, backups)


class ScheduleRecurrence(str, PyEnum):
    """Schedule recurrence types."""

    ONCE = "once"  # One-time schedule
    DAILY = "daily"  # Repeat daily
    WEEKLY = "weekly"  # Repeat weekly
    MONTHLY = "monthly"  # Repeat monthly


class BandwidthQuota(Base):
    """Bandwidth quota limits for devices or users."""

    __tablename__ = "bandwidth_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True
    )
    quota_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quota_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="monthly"
    )  # daily, weekly, monthly
    limit_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    used_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reset_day: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Day of month/week for reset
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    warning_threshold_percent: Mapped[int] = mapped_column(
        Integer, default=80, nullable=False
    )  # Alert at X%
    last_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    device = relationship("Device", back_populates="quotas")

    @property
    def usage_percent(self) -> float:
        """Calculate usage percentage."""
        if self.limit_bytes == 0:
            return 0.0
        return (self.used_bytes / self.limit_bytes) * 100

    @property
    def remaining_bytes(self) -> int:
        """Calculate remaining bytes."""
        return max(0, self.limit_bytes - self.used_bytes)

    def __repr__(self) -> str:
        """String representation."""
        return f"<BandwidthQuota(name={self.quota_name}, used={self.used_bytes}/{self.limit_bytes})>"


class QoSPolicy(Base):
    """Quality of Service policies for traffic prioritization."""

    __tablename__ = "qos_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[QoSPriority] = mapped_column(
        String(50), nullable=False, default=QoSPriority.MEDIUM, index=True
    )
    device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Traffic matching criteria
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    destination_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(10), nullable=True)  # tcp, udp, icmp
    # Bandwidth allocation
    min_bandwidth_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_bandwidth_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    guaranteed_bandwidth_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    device = relationship("Device", back_populates="qos_policies")

    def __repr__(self) -> str:
        """String representation."""
        return f"<QoSPolicy(name={self.policy_name}, priority={self.priority})>"


class ThrottleSchedule(Base):
    """Scheduled bandwidth throttling."""

    __tablename__ = "throttle_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    schedule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True
    )
    throttle_limit_mbps: Mapped[float] = mapped_column(Float, nullable=False)
    # Schedule timing
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    recurrence: Mapped[ScheduleRecurrence] = mapped_column(
        String(50), nullable=False, default=ScheduleRecurrence.DAILY
    )
    days_of_week: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Comma-separated: "0,1,2,3,4" (Mon-Fri)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    device = relationship("Device", back_populates="throttle_schedules")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ThrottleSchedule(name={self.schedule_name}, limit={self.throttle_limit_mbps}Mbps)>"
