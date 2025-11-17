"""Statistics endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device_repository import DeviceRepository
from src.schemas.device import DeviceStatistics
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/stats", response_model=DeviceStatistics)
async def get_overall_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall network statistics.
    
    Returns aggregated statistics for all devices including total bandwidth usage,
    active devices, blocked devices, etc.
    """
    repo = DeviceRepository(db)
    stats = await repo.get_statistics()
    
    return DeviceStatistics(**stats)


@router.get("/stats/top-consumers")
async def get_top_consumers(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get top bandwidth consumers.
    
    Returns list of devices consuming the most bandwidth.
    """
    repo = DeviceRepository(db)
    devices = await repo.get_top_consumers(limit=limit)
    
    return [
        {
            "id": device.id,
            "ip_address": device.ip_address,
            "mac_address": device.mac_address,
            "device_name": device.device_name,
            "total_bytes": device.total_bytes,
            "total_bytes_sent": device.total_bytes_sent,
            "total_bytes_received": device.total_bytes_received,
        }
        for device in devices
    ]
