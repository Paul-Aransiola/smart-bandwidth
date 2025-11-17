"""
Pytest fixtures for unit tests.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.core.database import Base, get_db
from src.main import app
from src.models.device import Device, DeviceStatus


@pytest.fixture
async def db_session():
    """Create an in-memory database session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Override the get_db dependency
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        
        yield session
        
        # Cleanup
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.fixture
def sample_device():
    """Create a sample device for testing."""
    return Device(
        id=1,
        ip_address="192.168.1.100",
        mac_address="00:11:22:33:44:55",
        hostname="test-device",
        device_name="Test Device",
        status=DeviceStatus.ACTIVE,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        is_blocked=False,
        is_throttled=False,
        throttle_limit_mbps=None,
        total_bytes_sent=1000000,
        total_bytes_received=2000000,
        notes="Test device",
    )


@pytest.fixture
def mock_bandwidth_controller():
    """Create a mock bandwidth controller."""
    controller = Mock()
    controller.block_device = AsyncMock(return_value=True)
    controller.unblock_device = AsyncMock(return_value=True)
    controller.throttle_device = AsyncMock(return_value=True)
    controller.unthrottle_device = AsyncMock(return_value=True)
    return controller
