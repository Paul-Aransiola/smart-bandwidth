"""
Database models for bandwidth monitoring.
Follows SQLAlchemy 2.0 style with proper typing.
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


class DeviceStatus(str, PyEnum):
    """Device connection status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    THROTTLED = "throttled"


class Device(Base):
    """
    Device model representing a connected network device.
    """

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, index=True, nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), unique=True, index=True, nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus),
        default=DeviceStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_throttled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    throttle_limit_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_bytes_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    bandwidth_usage = relationship(
        "BandwidthUsage",
        back_populates="device",
        cascade="all, delete-orphan",
    )
    block_history = relationship(
        "BlockHistory",
        back_populates="device",
        cascade="all, delete-orphan",
    )
    alert_rules = relationship(
        "AlertRule",
        back_populates="device",
        cascade="all, delete-orphan",
    )
    alerts = relationship(
        "Alert",
        back_populates="device",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_device_status_last_seen", "status", "last_seen"),
        Index("idx_device_ip_mac", "ip_address", "mac_address"),
    )

    @property
    def total_bytes(self) -> int:
        """Calculate total bytes transferred."""
        return self.total_bytes_sent + self.total_bytes_received

    def __repr__(self) -> str:
        """String representation."""
        return f"<Device(ip={self.ip_address}, mac={self.mac_address}, status={self.status})>"


class BandwidthUsage(Base):
    """
    Bandwidth usage records for devices.
    Stores time-series data of bandwidth consumption.
    """

    __tablename__ = "bandwidth_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    bytes_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    packets_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    packets_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upload_speed_mbps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    download_speed_mbps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    device = relationship("Device", back_populates="bandwidth_usage")

    # Indexes for time-series queries
    __table_args__ = (
        Index("idx_usage_device_timestamp", "device_id", "timestamp"),
        Index("idx_usage_timestamp", "timestamp"),
    )

    @property
    def total_bytes(self) -> int:
        """Calculate total bytes in this record."""
        return self.bytes_sent + self.bytes_received

    @property
    def total_speed_mbps(self) -> float:
        """Calculate total speed in Mbps."""
        return self.upload_speed_mbps + self.download_speed_mbps

    def __repr__(self) -> str:
        """String representation."""
        return f"<BandwidthUsage(device_id={self.device_id}, timestamp={self.timestamp})>"


class BlockHistory(Base):
    """
    History of device blocking/unblocking actions.
    Provides audit trail for bandwidth control actions.
    """

    __tablename__ = "block_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'block', 'unblock', 'throttle', 'unthrottle'
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    throttle_limit_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="block_history")

    # Indexes
    __table_args__ = (
        Index("idx_history_device_created", "device_id", "created_at"),
        Index("idx_history_action", "action"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<BlockHistory(device_id={self.device_id}, action={self.action})>"
