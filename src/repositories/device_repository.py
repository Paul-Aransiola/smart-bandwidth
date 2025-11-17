"""
Device repository for data access.
Implements specific queries for device management.
"""

from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.device import BlockHistory, Device, DeviceStatus
from src.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    """Repository for device data access."""

    def __init__(self, session: AsyncSession):
        """Initialize device repository."""
        super().__init__(session, Device)

    async def get_by_ip(self, ip_address: str) -> Device | None:
        """
        Get device by IP address.

        Args:
            ip_address: Device IP address

        Returns:
            Device instance or None
        """
        result = await self.session.execute(select(Device).where(Device.ip_address == ip_address))
        return result.scalar_one_or_none()

    async def get_by_mac(self, mac_address: str) -> Device | None:
        """
        Get device by MAC address.

        Args:
            mac_address: Device MAC address

        Returns:
            Device instance or None
        """
        result = await self.session.execute(select(Device).where(Device.mac_address == mac_address))
        return result.scalar_one_or_none()

    async def get_by_status(
        self, status: DeviceStatus, skip: int = 0, limit: int = 100
    ) -> list[Device]:
        """
        Get devices by status.

        Args:
            status: Device status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of devices
        """
        result = await self.session.execute(
            select(Device).where(Device.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_devices(self, minutes: int = 5) -> list[Device]:
        """
        Get devices active in the last N minutes.

        Args:
            minutes: Number of minutes to look back

        Returns:
            List of active devices
        """
        threshold = datetime.now() - timedelta(minutes=minutes)
        result = await self.session.execute(
            select(Device).where(
                and_(Device.last_seen >= threshold, Device.status == DeviceStatus.ACTIVE)
            )
        )
        return list(result.scalars().all())

    async def get_blocked_devices(self) -> list[Device]:
        """
        Get all blocked devices.

        Returns:
            List of blocked devices
        """
        result = await self.session.execute(
            select(Device).where(Device.is_blocked == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_throttled_devices(self) -> list[Device]:
        """
        Get all throttled devices.

        Returns:
            List of throttled devices
        """
        result = await self.session.execute(
            select(Device).where(Device.is_throttled == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def search_devices(self, query: str, skip: int = 0, limit: int = 100) -> list[Device]:
        """
        Search devices by IP, MAC, hostname, or device name.

        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching devices
        """
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Device)
            .where(
                or_(
                    Device.ip_address.like(search_pattern),
                    Device.mac_address.like(search_pattern),
                    Device.hostname.like(search_pattern),
                    Device.device_name.like(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_top_consumers(self, limit: int = 10) -> list[Device]:
        """
        Get top bandwidth consumers.

        Args:
            limit: Number of top consumers to return

        Returns:
            List of top consuming devices
        """
        result = await self.session.execute(
            select(Device)
            .order_by((Device.total_bytes_sent + Device.total_bytes_received).desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_seen(self, device: Device) -> Device:
        """
        Update device last seen timestamp.

        Args:
            device: Device to update

        Returns:
            Updated device
        """
        device.last_seen = datetime.now()
        return await self.update(device)

    async def update_bandwidth_totals(
        self, device: Device, bytes_sent: int, bytes_received: int
    ) -> Device:
        """
        Update device bandwidth totals.

        Args:
            device: Device to update
            bytes_sent: Bytes sent to add
            bytes_received: Bytes received to add

        Returns:
            Updated device
        """
        device.total_bytes_sent += bytes_sent
        device.total_bytes_received += bytes_received
        device.last_seen = datetime.now()
        return await self.update(device)

    async def get_statistics(self) -> dict:
        """
        Get device statistics.

        Returns:
            Dictionary with device statistics
        """
        total = await self.session.execute(select(func.count()).select_from(Device))
        active = await self.session.execute(
            select(func.count()).select_from(Device).where(Device.status == DeviceStatus.ACTIVE)
        )
        blocked = await self.session.execute(
            select(func.count()).select_from(Device).where(Device.is_blocked == True)  # noqa: E712
        )
        throttled = await self.session.execute(
            select(func.count()).select_from(Device).where(Device.is_throttled == True)  # noqa: E712
        )
        total_bandwidth = await self.session.execute(
            select(func.sum(Device.total_bytes_sent + Device.total_bytes_received))
        )

        return {
            "total_devices": total.scalar_one(),
            "active_devices": active.scalar_one(),
            "blocked_devices": blocked.scalar_one(),
            "throttled_devices": throttled.scalar_one(),
            "total_bandwidth_used": total_bandwidth.scalar_one() or 0,
        }


class BlockHistoryRepository(BaseRepository[BlockHistory]):
    """Repository for block history data access."""

    def __init__(self, session: AsyncSession):
        """Initialize block history repository."""
        super().__init__(session, BlockHistory)

    async def get_by_device(
        self, device_id: int, skip: int = 0, limit: int = 100
    ) -> list[BlockHistory]:
        """
        Get block history for a device.

        Args:
            device_id: Device ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of block history records
        """
        result = await self.session.execute(
            select(BlockHistory)
            .where(BlockHistory.device_id == device_id)
            .order_by(BlockHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_device_history(
        self, device_id: int, limit: int = 50
    ) -> list[BlockHistory]:
        """
        Get block history for a device (alias for get_by_device).

        Args:
            device_id: Device ID
            limit: Maximum number of records

        Returns:
            List of block history records
        """
        return await self.get_by_device(device_id, limit=limit)

    async def get_recent_actions(
        self, hours: int = 24, skip: int = 0, limit: int = 100
    ) -> list[BlockHistory]:
        """
        Get recent block/unblock actions.

        Args:
            hours: Number of hours to look back
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of recent block history records
        """
        threshold = datetime.now() - timedelta(hours=hours)
        result = await self.session.execute(
            select(BlockHistory)
            .where(BlockHistory.created_at >= threshold)
            .order_by(BlockHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
