"""
Device service for orchestrating device operations.

This service layer coordinates between repositories and provides
business logic for device management operations.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DeviceNotFoundException
from src.models.device import Device, DeviceStatus
from src.repositories.bandwidth_repository import BandwidthUsageRepository
from src.repositories.device_repository import DeviceRepository
from src.schemas.device import DeviceCreate, DeviceUpdate
from src.services.bandwidth_controller import BandwidthController
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DeviceService:
    """Service for managing devices and their operations."""

    def __init__(
        self,
        session: AsyncSession,
        bandwidth_controller: BandwidthController | None = None,
    ):
        """
        Initialize device service.

        Args:
            session: Database session
            bandwidth_controller: Optional bandwidth controller (for testing)
        """
        self.session = session
        self.device_repo = DeviceRepository(session)
        self.bandwidth_repo = BandwidthUsageRepository(session)
        self.bandwidth_controller = bandwidth_controller or BandwidthController()

    async def get_device_by_ip(self, ip_address: str) -> Device:
        """
        Get device by IP address.

        Args:
            ip_address: IP address of the device

        Returns:
            Device object

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.device_repo.get_by_ip(ip_address)
        if not device:
            raise DeviceNotFoundException(f"Device with IP {ip_address} not found")
        return device

    async def get_device_by_mac(self, mac_address: str) -> Device:
        """
        Get device by MAC address.

        Args:
            mac_address: MAC address of the device

        Returns:
            Device object

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.device_repo.get_by_mac(mac_address)
        if not device:
            raise DeviceNotFoundException(f"Device with MAC {mac_address} not found")
        return device

    async def list_devices(
        self,
        skip: int = 0,
        limit: int = 100,
        status: DeviceStatus | None = None,
    ) -> list[Device]:
        """
        List devices with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of devices
        """
        if status:
            return await self.device_repo.get_by_status(status, skip, limit)
        return await self.device_repo.get_all(skip, limit)

    async def create_device(self, device_data: DeviceCreate) -> Device:
        """
        Create a new device.

        Args:
            device_data: Device creation data

        Returns:
            Created device
        """
        # Check if device already exists
        existing_device = await self.device_repo.get_by_ip(device_data.ip_address)
        if existing_device:
            logger.warning(f"Device with IP {device_data.ip_address} already exists")
            return existing_device

        # Create new device
        device = Device(
            ip_address=device_data.ip_address,
            mac_address=device_data.mac_address,
            hostname=device_data.hostname,
            device_name=device_data.device_name,
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=0,
            total_bytes_received=0,
            notes=device_data.notes,
        )
        created_device = await self.device_repo.create(device)
        logger.info(f"Created device: {created_device.ip_address}")
        return created_device

    async def update_device(self, ip_address: str, device_data: DeviceUpdate) -> Device:
        """
        Update device information.

        Args:
            ip_address: IP address of the device
            device_data: Device update data

        Returns:
            Updated device

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.get_device_by_ip(ip_address)

        # Update fields
        update_dict = device_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(device, field, value)

        device.last_seen = datetime.now()
        updated_device = await self.device_repo.update(device)
        logger.info(f"Updated device: {updated_device.ip_address}")
        return updated_device

    async def delete_device(self, ip_address: str) -> bool:
        """
        Delete a device.

        Args:
            ip_address: IP address of the device

        Returns:
            True if deleted successfully

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.get_device_by_ip(ip_address)

        # Clean up any active blocks or throttles
        if device.is_blocked:
            try:
                await self.bandwidth_controller.unblock_device(device.ip_address)
            except Exception as e:
                logger.warning(f"Failed to unblock device before deletion: {e}")

        if device.is_throttled:
            try:
                await self.bandwidth_controller.unthrottle_device(device.ip_address)
            except Exception as e:
                logger.warning(f"Failed to unthrottle device before deletion: {e}")

        # Delete device
        await self.device_repo.delete(device)
        logger.info(f"Deleted device: {ip_address}")
        return True

    async def update_device_bandwidth(
        self, ip_address: str, bytes_sent: int, bytes_received: int
    ) -> Device:
        """
        Update device bandwidth statistics.

        Args:
            ip_address: IP address of the device
            bytes_sent: Bytes sent since last update
            bytes_received: Bytes received since last update

        Returns:
            Updated device

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.get_device_by_ip(ip_address)

        device.total_bytes_sent += bytes_sent
        device.total_bytes_received += bytes_received
        device.last_seen = datetime.now()

        updated_device = await self.device_repo.update(device)
        logger.debug(
            f"Updated bandwidth for {ip_address}: +{bytes_sent} sent, +{bytes_received} received"
        )
        return updated_device

    async def mark_device_offline(self, ip_address: str) -> Device:
        """
        Mark a device as offline.

        Args:
            ip_address: IP address of the device

        Returns:
            Updated device

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.get_device_by_ip(ip_address)
        device.status = DeviceStatus.INACTIVE
        updated_device = await self.device_repo.update(device)
        logger.info(f"Marked device offline: {ip_address}")
        return updated_device

    async def mark_device_active(self, ip_address: str) -> Device:
        """
        Mark a device as active.

        Args:
            ip_address: IP address of the device

        Returns:
            Updated device

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.get_device_by_ip(ip_address)
        device.status = DeviceStatus.ACTIVE
        device.last_seen = datetime.now()
        updated_device = await self.device_repo.update(device)
        logger.info(f"Marked device active: {ip_address}")
        return updated_device

    async def get_device_statistics(self, ip_address: str) -> dict:
        """
        Get comprehensive statistics for a device.

        Args:
            ip_address: IP address of the device

        Returns:
            Dictionary with device statistics

        Raises:
            DeviceNotFoundException: If device not found
        """
        device = await self.get_device_by_ip(ip_address)

        # Get bandwidth history
        bandwidth_history = await self.bandwidth_repo.get_by_device(device.id, limit=100)

        # Calculate statistics
        total_bandwidth = device.total_bytes_sent + device.total_bytes_received
        total_bandwidth_mb = total_bandwidth / (1024 * 1024)

        return {
            "device_info": {
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "hostname": device.hostname,
                "device_name": device.device_name,
                "status": device.status.value,
            },
            "bandwidth": {
                "total_sent_bytes": device.total_bytes_sent,
                "total_received_bytes": device.total_bytes_received,
                "total_bytes": total_bandwidth,
                "total_mb": round(total_bandwidth_mb, 2),
            },
            "control_status": {
                "is_blocked": device.is_blocked,
                "is_throttled": device.is_throttled,
                "throttle_limit_mbps": device.throttle_limit_mbps,
            },
            "history_count": len(bandwidth_history),
            "first_seen": device.first_seen.isoformat() if device.first_seen else None,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }

    async def get_all_statistics(self) -> dict:
        """
        Get overall statistics for all devices.

        Returns:
            Dictionary with overall statistics
        """
        devices = await self.device_repo.get_all(skip=0, limit=1000)

        total_devices = len(devices)
        active_devices = sum(1 for d in devices if d.status == DeviceStatus.ACTIVE)
        blocked_devices = sum(1 for d in devices if d.is_blocked)
        throttled_devices = sum(1 for d in devices if d.is_throttled)

        total_bandwidth = sum(d.total_bytes_sent + d.total_bytes_received for d in devices)
        total_bandwidth_gb = total_bandwidth / (1024 * 1024 * 1024)

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "blocked_devices": blocked_devices,
            "throttled_devices": throttled_devices,
            "total_bandwidth_gb": round(total_bandwidth_gb, 2),
        }
