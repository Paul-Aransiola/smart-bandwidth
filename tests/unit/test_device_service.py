"""
Unit tests for DeviceService.
"""

from datetime import datetime

import pytest

from src.core.exceptions import DeviceNotFoundException
from src.models.device import Device, DeviceStatus
from src.schemas.device import DeviceCreate, DeviceUpdate
from src.services.device_service import DeviceService


@pytest.mark.asyncio
class TestDeviceServiceGetMethods:
    """Tests for device retrieval methods."""

    async def test_get_device_by_ip_success(self, db_session, sample_device):
        """Test getting device by IP address."""
        # Create device in database
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        # Test service
        service = DeviceService(db_session)
        result = await service.get_device_by_ip(sample_device.ip_address)

        assert result.ip_address == sample_device.ip_address
        assert result.mac_address == sample_device.mac_address

    async def test_get_device_by_ip_not_found(self, db_session):
        """Test getting nonexistent device by IP."""
        service = DeviceService(db_session)

        with pytest.raises(DeviceNotFoundException):
            await service.get_device_by_ip("192.168.1.999")

    async def test_get_device_by_mac_success(self, db_session, sample_device):
        """Test getting device by MAC address."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        service = DeviceService(db_session)
        result = await service.get_device_by_mac(sample_device.mac_address)

        assert result.mac_address == sample_device.mac_address
        assert result.ip_address == sample_device.ip_address

    async def test_get_device_by_mac_not_found(self, db_session):
        """Test getting nonexistent device by MAC."""
        service = DeviceService(db_session)

        with pytest.raises(DeviceNotFoundException):
            await service.get_device_by_mac("FF:FF:FF:FF:FF:FF")


@pytest.mark.asyncio
class TestDeviceServiceListMethods:
    """Tests for device listing methods."""

    async def test_list_devices_all(self, db_session):
        """Test listing all devices."""
        from src.repositories.device_repository import DeviceRepository

        # Create multiple devices
        repo = DeviceRepository(db_session)
        for i in range(5):
            device = Device(
                ip_address=f"192.168.1.{100 + i}",
                mac_address=f"00:11:22:33:44:{i:02X}",
                hostname=f"device-{i}",
                device_name=f"Device {i}",
                status=DeviceStatus.ACTIVE,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                is_blocked=False,
                is_throttled=False,
                total_bytes_sent=0,
                total_bytes_received=0,
            )
            await repo.create(device)

        # List all devices
        service = DeviceService(db_session)
        devices = await service.list_devices()

        assert len(devices) == 5

    async def test_list_devices_with_pagination(self, db_session):
        """Test listing devices with pagination."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        for i in range(10):
            device = Device(
                ip_address=f"192.168.1.{100 + i}",
                mac_address=f"00:11:22:33:44:{i:02X}",
                hostname=f"device-{i}",
                device_name=f"Device {i}",
                status=DeviceStatus.ACTIVE,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                is_blocked=False,
                is_throttled=False,
                total_bytes_sent=0,
                total_bytes_received=0,
            )
            await repo.create(device)

        service = DeviceService(db_session)
        devices = await service.list_devices(skip=5, limit=3)

        assert len(devices) == 3

    async def test_list_devices_by_status(self, db_session):
        """Test listing devices filtered by status."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        # Create active devices
        for i in range(3):
            device = Device(
                ip_address=f"192.168.1.{100 + i}",
                mac_address=f"00:11:22:33:44:{i:02X}",
                hostname=f"active-{i}",
                device_name=f"Active {i}",
                status=DeviceStatus.ACTIVE,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                is_blocked=False,
                is_throttled=False,
                total_bytes_sent=0,
                total_bytes_received=0,
            )
            await repo.create(device)

        # Create blocked devices
        for i in range(2):
            device = Device(
                ip_address=f"192.168.1.{200 + i}",
                mac_address=f"00:11:22:33:55:{i:02X}",
                hostname=f"blocked-{i}",
                device_name=f"Blocked {i}",
                status=DeviceStatus.BLOCKED,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                is_blocked=True,
                is_throttled=False,
                total_bytes_sent=0,
                total_bytes_received=0,
            )
            await repo.create(device)

        service = DeviceService(db_session)
        active_devices = await service.list_devices(status=DeviceStatus.ACTIVE)
        blocked_devices = await service.list_devices(status=DeviceStatus.BLOCKED)

        assert len(active_devices) == 3
        assert len(blocked_devices) == 2


@pytest.mark.asyncio
class TestDeviceServiceCRUD:
    """Tests for device CRUD operations."""

    async def test_create_device_success(self, db_session):
        """Test creating a new device."""
        device_data = DeviceCreate(
            ip_address="192.168.1.50",
            mac_address="AA:BB:CC:DD:EE:FF",
            hostname="new-device",
            device_name="New Device",
            notes="Test device",
        )

        service = DeviceService(db_session)
        device = await service.create_device(device_data)

        assert device.ip_address == "192.168.1.50"
        assert device.mac_address == "AA:BB:CC:DD:EE:FF"
        assert device.status == DeviceStatus.ACTIVE
        assert device.is_blocked is False
        assert device.is_throttled is False

    async def test_create_device_already_exists(self, db_session, sample_device):
        """Test creating device that already exists."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        device_data = DeviceCreate(
            ip_address=sample_device.ip_address,
            mac_address=sample_device.mac_address,
            hostname="duplicate",
            device_name="Duplicate",
        )

        service = DeviceService(db_session)
        result = await service.create_device(device_data)

        # Should return existing device
        assert result.ip_address == sample_device.ip_address

    async def test_update_device_success(self, db_session, sample_device):
        """Test updating device information."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        update_data = DeviceUpdate(device_name="Updated Name", notes="Updated notes")

        service = DeviceService(db_session)
        updated = await service.update_device(sample_device.ip_address, update_data)

        assert updated.device_name == "Updated Name"
        assert updated.notes == "Updated notes"

    async def test_update_device_not_found(self, db_session):
        """Test updating nonexistent device."""
        update_data = DeviceUpdate(device_name="New Name")

        service = DeviceService(db_session)

        with pytest.raises(DeviceNotFoundException):
            await service.update_device("192.168.1.999", update_data)

    async def test_delete_device_success(
        self, db_session, sample_device, mock_bandwidth_controller
    ):
        """Test deleting a device."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        service = DeviceService(db_session, bandwidth_controller=mock_bandwidth_controller)
        result = await service.delete_device(sample_device.ip_address)

        assert result is True

        # Verify device is deleted
        with pytest.raises(DeviceNotFoundException):
            await service.get_device_by_ip(sample_device.ip_address)

    async def test_delete_device_with_active_block(self, db_session, mock_bandwidth_controller):
        """Test deleting device with active block."""
        from src.repositories.device_repository import DeviceRepository

        # Create blocked device
        device = Device(
            ip_address="192.168.1.50",
            mac_address="AA:BB:CC:DD:EE:FF",
            hostname="blocked-device",
            device_name="Blocked Device",
            status=DeviceStatus.BLOCKED,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=True,
            is_throttled=False,
            total_bytes_sent=0,
            total_bytes_received=0,
        )
        repo = DeviceRepository(db_session)
        await repo.create(device)

        service = DeviceService(db_session, bandwidth_controller=mock_bandwidth_controller)
        result = await service.delete_device(device.ip_address)

        assert result is True
        mock_bandwidth_controller.unblock_device.assert_called_once()


@pytest.mark.asyncio
class TestDeviceServiceBandwidth:
    """Tests for bandwidth-related methods."""

    async def test_update_device_bandwidth(self, db_session, sample_device):
        """Test updating device bandwidth statistics."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        created_device = await repo.create(sample_device)

        initial_sent = created_device.total_bytes_sent
        initial_received = created_device.total_bytes_received

        service = DeviceService(db_session)
        updated = await service.update_device_bandwidth(
            sample_device.ip_address, bytes_sent=1000000, bytes_received=2000000
        )

        assert updated.total_bytes_sent == initial_sent + 1000000
        assert updated.total_bytes_received == initial_received + 2000000


@pytest.mark.asyncio
class TestDeviceServiceStatus:
    """Tests for device status methods."""

    async def test_mark_device_offline(self, db_session, sample_device):
        """Test marking device as offline."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        service = DeviceService(db_session)
        updated = await service.mark_device_offline(sample_device.ip_address)

        assert updated.status == DeviceStatus.INACTIVE

    async def test_mark_device_active(self, db_session, sample_device):
        """Test marking device as active."""
        from src.repositories.device_repository import DeviceRepository

        # Create inactive device
        sample_device.status = DeviceStatus.INACTIVE
        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        service = DeviceService(db_session)
        updated = await service.mark_device_active(sample_device.ip_address)

        assert updated.status == DeviceStatus.ACTIVE


@pytest.mark.asyncio
class TestDeviceServiceStatistics:
    """Tests for statistics methods."""

    async def test_get_device_statistics(self, db_session, sample_device):
        """Test getting device statistics."""
        from src.repositories.device_repository import DeviceRepository

        repo = DeviceRepository(db_session)
        await repo.create(sample_device)

        service = DeviceService(db_session)
        stats = await service.get_device_statistics(sample_device.ip_address)

        assert "device_info" in stats
        assert "bandwidth" in stats
        assert "control_status" in stats
        assert stats["device_info"]["ip_address"] == sample_device.ip_address
        assert stats["bandwidth"]["total_sent_bytes"] == sample_device.total_bytes_sent
        assert stats["control_status"]["is_blocked"] == sample_device.is_blocked

    async def test_get_all_statistics(self, db_session):
        """Test getting overall statistics."""
        from src.repositories.device_repository import DeviceRepository

        # Create test devices
        repo = DeviceRepository(db_session)
        for i in range(5):
            device = Device(
                ip_address=f"192.168.1.{100 + i}",
                mac_address=f"00:11:22:33:44:{i:02X}",
                hostname=f"device-{i}",
                device_name=f"Device {i}",
                status=DeviceStatus.ACTIVE if i < 3 else DeviceStatus.BLOCKED,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                is_blocked=(i >= 3),
                is_throttled=(i == 2),
                total_bytes_sent=1000000 * (i + 1),
                total_bytes_received=2000000 * (i + 1),
            )
            await repo.create(device)

        service = DeviceService(db_session)
        stats = await service.get_all_statistics()

        assert stats["total_devices"] == 5
        assert stats["active_devices"] == 3
        assert stats["blocked_devices"] == 2
        assert stats["throttled_devices"] == 1
        assert stats["total_bandwidth_gb"] > 0
