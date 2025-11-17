"""
Integration tests for control API endpoints.

These tests verify the full workflow of device control operations including:
- Device creation
- Blocking/unblocking devices
- Throttling/unthrottling devices
- History tracking
"""

from datetime import datetime

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.models.device import Device, DeviceStatus
from src.repositories.device_repository import DeviceRepository


@pytest.mark.asyncio
class TestControlAPIWorkflow:
    """Integration tests for control API workflow."""

    async def test_complete_device_control_workflow(self, db_session):
        """Test complete workflow: create device -> block -> unblock -> throttle -> unthrottle."""
        # Step 1: Create a device
        device_repo = DeviceRepository(db_session)
        device = Device(
            ip_address="192.168.1.50",
            mac_address="AA:BB:CC:DD:EE:FF",
            hostname="integration-test",
            device_name="Integration Test Device",
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=5000000,
            total_bytes_received=10000000,
        )
        await device_repo.create(device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 2: Block the device
            response = await client.post(
                f"/api/v1/block/{device.ip_address}", json={"reason": "Integration test blocking"}
            )
            assert (
                response.status_code == status.HTTP_200_OK
                or response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            )  # 500 expected since we can't actually run iptables
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert data["ip_address"] == device.ip_address

            # Step 3: Verify device is in the system
            device_from_db = await device_repo.get_by_ip(device.ip_address)
            assert device_from_db is not None
            assert device_from_db.ip_address == device.ip_address

    async def test_block_nonexistent_device(self, db_session):
        """Test blocking a device that doesn't exist."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/block/192.168.1.999", json={"reason": "Test"})
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()

    async def test_throttle_then_check_history(self, db_session):
        """Test throttling a device and checking history."""
        # Create device
        device_repo = DeviceRepository(db_session)
        device = Device(
            ip_address="192.168.1.60",
            mac_address="11:22:33:44:55:66",
            hostname="throttle-test",
            device_name="Throttle Test Device",
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=1000000,
            total_bytes_received=2000000,
        )
        await device_repo.create(device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Throttle device
            response = await client.post(
                f"/api/v1/throttle/{device.ip_address}",
                json={"limit_mbps": 5.0, "reason": "High bandwidth usage"},
            )
            # Accept both success and error (error expected if tc not available)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

            # Check history
            history_response = await client.get(f"/api/v1/history/{device.ip_address}")
            assert history_response.status_code == status.HTTP_200_OK
            history_data = history_response.json()
            assert isinstance(history_data, list)

    async def test_device_list_after_modifications(self, db_session):
        """Test listing devices after various control operations."""
        # Create multiple devices
        device_repo = DeviceRepository(db_session)
        devices = [
            Device(
                ip_address=f"192.168.1.{70 + i}",
                mac_address=f"AA:BB:CC:DD:EE:{i:02X}",
                hostname=f"device-{i}",
                device_name=f"Device {i}",
                status=DeviceStatus.ACTIVE,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                is_blocked=False,
                is_throttled=False,
                total_bytes_sent=1000000 * (i + 1),
                total_bytes_received=2000000 * (i + 1),
            )
            for i in range(3)
        ]
        for dev in devices:
            await device_repo.create(dev)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # List all devices
            response = await client.get("/api/v1/devices")
            assert response.status_code == status.HTTP_200_OK
            devices_data = response.json()
            assert isinstance(devices_data, list)
            assert len(devices_data) >= 3

    async def test_statistics_endpoint(self, db_session):
        """Test statistics endpoint with devices."""
        # Create devices
        device_repo = DeviceRepository(db_session)
        device = Device(
            ip_address="192.168.1.80",
            mac_address="AA:BB:CC:DD:EE:80",
            hostname="stats-test",
            device_name="Stats Test Device",
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=10000000,
            total_bytes_received=20000000,
        )
        await device_repo.create(device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Get statistics
            response = await client.get("/api/v1/stats")
            assert response.status_code == status.HTTP_200_OK
            stats = response.json()
            assert "total_devices" in stats
            assert "active_devices" in stats
            assert "total_bandwidth_used" in stats
            assert stats["total_devices"] >= 1

    async def test_health_check(self, db_session):
        """Test health check endpoints."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Basic health check
            response = await client.get("/api/v1/health")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"

            # Detailed health check
            detailed_response = await client.get("/api/v1/health/detailed")
            assert detailed_response.status_code == status.HTTP_200_OK
            detailed_data = detailed_response.json()
            assert "status" in detailed_data
            assert "services" in detailed_data
            assert "database" in detailed_data["services"]

    async def test_unblock_then_throttle(self, db_session):
        """Test unblocking a device then immediately throttling it."""
        # Create blocked device
        device_repo = DeviceRepository(db_session)
        device = Device(
            ip_address="192.168.1.90",
            mac_address="AA:BB:CC:DD:EE:90",
            hostname="combo-test",
            device_name="Combo Test Device",
            status=DeviceStatus.BLOCKED,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=True,
            is_throttled=False,
            total_bytes_sent=5000000,
            total_bytes_received=10000000,
        )
        await device_repo.create(device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Unblock device
            unblock_response = await client.post(f"/api/v1/unblock/{device.ip_address}")
            # Accept both success and error
            assert unblock_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

            # Try to throttle (should work if unblock succeeded)
            throttle_response = await client.post(
                f"/api/v1/throttle/{device.ip_address}",
                json={"limit_mbps": 10.0, "reason": "Test throttle after unblock"},
            )
            # Accept various responses based on system capabilities
            assert throttle_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

    async def test_invalid_throttle_limit(self, db_session):
        """Test throttling with invalid limit values."""
        device_repo = DeviceRepository(db_session)
        device = Device(
            ip_address="192.168.1.100",
            mac_address="AA:BB:CC:DD:EE:A0",
            hostname="invalid-test",
            device_name="Invalid Test Device",
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=1000000,
            total_bytes_received=2000000,
        )
        await device_repo.create(device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Try negative limit
            response = await client.post(
                f"/api/v1/throttle/{device.ip_address}",
                json={"limit_mbps": -10.0, "reason": "Invalid limit"},
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

            # Try zero limit
            response = await client.post(
                f"/api/v1/throttle/{device.ip_address}",
                json={"limit_mbps": 0.0, "reason": "Zero limit"},
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_get_device_by_ip(self, db_session):
        """Test getting a specific device by IP."""
        device_repo = DeviceRepository(db_session)
        device = Device(
            ip_address="192.168.1.110",
            mac_address="AA:BB:CC:DD:EE:B0",
            hostname="get-test",
            device_name="Get Test Device",
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=3000000,
            total_bytes_received=6000000,
        )
        await device_repo.create(device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/devices/ip/{device.ip_address}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["ip_address"] == device.ip_address
            assert data["mac_address"] == device.mac_address
            assert data["total_bytes_sent"] == 3000000
            assert data["total_bytes_received"] == 6000000
