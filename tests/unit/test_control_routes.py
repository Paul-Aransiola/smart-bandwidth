"""
Unit tests for control endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.models.device import BlockHistory, DeviceStatus
from src.repositories.device_repository import BlockHistoryRepository, DeviceRepository


@pytest.mark.asyncio
class TestBlockDevice:
    """Tests for block_device endpoint."""

    async def test_block_device_success(self, db_session, sample_device):
        """Test successful device blocking."""
        # Setup
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        # Mock BandwidthController
        with patch("src.api.routes.control.BandwidthController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.block_device = AsyncMock(return_value=True)
            mock_controller_class.return_value = mock_controller

            # Make request
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/block/{sample_device.ip_address}",
                    json={"reason": "Test blocking"},
                )

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["success"] is True
            data = response_data["data"]
            assert data["ip_address"] == sample_device.ip_address
            assert data["is_blocked"] is True
            assert data["status"] == "blocked"

            # Verify controller was called
            mock_controller.block_device.assert_called_once_with(sample_device.ip_address)

    async def test_block_device_not_found(self, db_session):
        """Test blocking a non-existent device."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/block/192.168.1.999", json={"reason": "Test"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_block_device_already_blocked(self, db_session, sample_device):
        """Test blocking an already blocked device."""
        # Setup
        sample_device.is_blocked = True
        sample_device.status = DeviceStatus.BLOCKED
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/block/{sample_device.ip_address}",
                json={"reason": "Test blocking"},
            )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        data = response_data["data"]
        assert data["is_blocked"] is True

    async def test_block_device_controller_failure(self, db_session, sample_device):
        """Test handling of controller failure during blocking."""
        # Setup
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        # Mock controller to raise exception
        with patch("src.api.routes.control.BandwidthController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.block_device = AsyncMock(return_value=False)
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/block/{sample_device.ip_address}",
                    json={"reason": "Test blocking"},
                )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
class TestUnblockDevice:
    """Tests for unblock_device endpoint."""

    async def test_unblock_device_success(self, db_session, sample_device):
        """Test successful device unblocking."""
        # Setup blocked device
        sample_device.is_blocked = True
        sample_device.status = DeviceStatus.BLOCKED
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        # Mock dependencies
        with patch("src.api.routes.control.BandwidthController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.unblock_device = AsyncMock(return_value=True)
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(f"/api/v1/unblock/{sample_device.ip_address}")

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["success"] is True
            data = response_data["data"]
            assert data["ip_address"] == sample_device.ip_address
            assert data["is_blocked"] is False
            assert data["status"] == "active"

            mock_controller.unblock_device.assert_called_once_with(sample_device.ip_address)

    async def test_unblock_device_not_found(self, db_session):
        """Test unblocking a non-existent device."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/unblock/192.168.1.999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_unblock_device_not_blocked(self, db_session, sample_device):
        """Test unblocking a device that is not blocked."""
        # Setup
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/v1/unblock/{sample_device.ip_address}")

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        data = response_data["data"]
        assert data["is_blocked"] is False


@pytest.mark.asyncio
class TestThrottleDevice:
    """Tests for throttle_device endpoint."""

    async def test_throttle_device_success(self, db_session, sample_device):
        """Test successful device throttling."""
        # Setup
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        # Mock dependencies
        with patch("src.api.routes.control.BandwidthController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.throttle_device = AsyncMock(return_value=True)
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/throttle/{sample_device.ip_address}",
                    json={"limit_mbps": 10.0, "reason": "High usage"},
                )

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["success"] is True
            data = response_data["data"]
            assert data["ip_address"] == sample_device.ip_address
            assert data["is_throttled"] is True
            assert data["throttle_limit_mbps"] == 10.0
            assert data["status"] == "throttled"

            mock_controller.throttle_device.assert_called_once_with(sample_device.ip_address, 10.0)

    async def test_throttle_device_not_found(self, db_session):
        """Test throttling a non-existent device."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/throttle/192.168.1.999",
                json={"limit_mbps": 10.0, "reason": "Test"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_throttle_blocked_device(self, db_session, sample_device):
        """Test throttling a blocked device should fail."""
        # Setup blocked device
        sample_device.is_blocked = True
        sample_device.status = DeviceStatus.BLOCKED
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/throttle/{sample_device.ip_address}",
                json={"limit_mbps": 10.0, "reason": "Test"},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "blocked" in response.json()["detail"].lower()

    async def test_throttle_invalid_limit(self, db_session, sample_device):
        """Test throttling with invalid limit."""
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/throttle/{sample_device.ip_address}",
                json={"limit_mbps": -5.0, "reason": "Test"},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestUnthrottleDevice:
    """Tests for unthrottle_device endpoint."""

    async def test_unthrottle_device_success(self, db_session, sample_device):
        """Test successful device unthrottling."""
        # Setup throttled device
        sample_device.is_throttled = True
        sample_device.throttle_limit_mbps = 10.0
        sample_device.status = DeviceStatus.THROTTLED
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        # Mock dependencies
        with patch("src.api.routes.control.BandwidthController") as mock_controller_class:
            mock_controller = Mock()
            mock_controller.unthrottle_device = AsyncMock(return_value=True)
            mock_controller_class.return_value = mock_controller

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(f"/api/v1/unthrottle/{sample_device.ip_address}")

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["success"] is True
            data = response_data["data"]
            assert data["ip_address"] == sample_device.ip_address
            assert data["is_throttled"] is False
            assert data["throttle_limit_mbps"] is None
            assert data["status"] == "active"

            mock_controller.unthrottle_device.assert_called_once_with(sample_device.ip_address)

    async def test_unthrottle_device_not_found(self, db_session):
        """Test unthrottling a non-existent device."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/unthrottle/192.168.1.999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_unthrottle_device_not_throttled(self, db_session, sample_device):
        """Test unthrottling a device that is not throttled."""
        # Setup
        device_repo = DeviceRepository(db_session)
        await device_repo.create(sample_device)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/v1/unthrottle/{sample_device.ip_address}")

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        data = response_data["data"]
        assert data["is_throttled"] is False


@pytest.mark.asyncio
class TestGetDeviceHistory:
    """Tests for get_device_history endpoint."""

    async def test_get_device_history_success(self, db_session, sample_device):
        """Test successful history retrieval."""
        # Setup device and history
        device_repo = DeviceRepository(db_session)
        history_repo = BlockHistoryRepository(db_session)
        await device_repo.create(sample_device)

        # Create some history records
        history1 = BlockHistory(
            device_id=sample_device.id,
            action="block",
            reason="High usage",
            created_at=datetime.now(),
        )
        history2 = BlockHistory(
            device_id=sample_device.id,
            action="unblock",
            created_at=datetime.now(),
        )
        await history_repo.create(history1)
        await history_repo.create(history2)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/history/{sample_device.ip_address}")

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        data = response_data["data"]
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["action"] in ["block", "unblock"]

    async def test_get_device_history_not_found(self, db_session):
        """Test history retrieval for non-existent device."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/history/192.168.1.999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_device_history_with_limit(self, db_session, sample_device):
        """Test history retrieval with custom limit."""
        # Setup device
        device_repo = DeviceRepository(db_session)
        history_repo = BlockHistoryRepository(db_session)
        await device_repo.create(sample_device)

        # Create multiple history records
        for i in range(10):
            history = BlockHistory(
                device_id=sample_device.id,
                action="block" if i % 2 == 0 else "unblock",
                created_at=datetime.now(),
            )
            await history_repo.create(history)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/history/{sample_device.ip_address}?limit=5")

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        data = response_data["data"]
        assert len(data) <= 5
