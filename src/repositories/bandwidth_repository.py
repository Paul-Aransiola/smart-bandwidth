"""
Bandwidth usage repository for data access.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.device import BandwidthUsage
from src.repositories.base import BaseRepository


class BandwidthUsageRepository(BaseRepository[BandwidthUsage]):
    """Repository for bandwidth usage data access."""

    def __init__(self, session: AsyncSession):
        """Initialize bandwidth usage repository."""
        super().__init__(session, BandwidthUsage)

    async def get_by_device(
        self, device_id: int, skip: int = 0, limit: int = 100
    ) -> list[BandwidthUsage]:
        """
        Get bandwidth usage records for a device.

        Args:
            device_id: Device ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of bandwidth usage records
        """
        result = await self.session.execute(
            select(BandwidthUsage)
            .where(BandwidthUsage.device_id == device_id)
            .order_by(BandwidthUsage.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_time_range(
        self, device_id: int, start_time: datetime, end_time: datetime
    ) -> list[BandwidthUsage]:
        """
        Get bandwidth usage for a device within a time range.

        Args:
            device_id: Device ID
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of bandwidth usage records
        """
        result = await self.session.execute(
            select(BandwidthUsage)
            .where(
                BandwidthUsage.device_id == device_id,
                BandwidthUsage.timestamp >= start_time,
                BandwidthUsage.timestamp <= end_time,
            )
            .order_by(BandwidthUsage.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_recent_usage(self, device_id: int, minutes: int = 60) -> list[BandwidthUsage]:
        """
        Get recent bandwidth usage for a device.

        Args:
            device_id: Device ID
            minutes: Number of minutes to look back

        Returns:
            List of recent bandwidth usage records
        """
        threshold = datetime.now() - timedelta(minutes=minutes)
        result = await self.session.execute(
            select(BandwidthUsage)
            .where(BandwidthUsage.device_id == device_id, BandwidthUsage.timestamp >= threshold)
            .order_by(BandwidthUsage.timestamp.desc())
        )
        return list(result.scalars().all())

    async def get_statistics(self, device_id: int) -> dict:
        """
        Get bandwidth statistics for a device.

        Args:
            device_id: Device ID

        Returns:
            Dictionary with bandwidth statistics
        """
        result = await self.session.execute(
            select(
                func.sum(BandwidthUsage.bytes_sent).label("total_sent"),
                func.sum(BandwidthUsage.bytes_received).label("total_received"),
                func.avg(BandwidthUsage.upload_speed_mbps).label("avg_upload"),
                func.avg(BandwidthUsage.download_speed_mbps).label("avg_download"),
                func.max(BandwidthUsage.upload_speed_mbps).label("peak_upload"),
                func.max(BandwidthUsage.download_speed_mbps).label("peak_download"),
                func.min(BandwidthUsage.timestamp).label("first_recorded"),
                func.max(BandwidthUsage.timestamp).label("last_recorded"),
            ).where(BandwidthUsage.device_id == device_id)
        )
        row = result.one_or_none()

        if not row or row.total_sent is None:
            return {
                "total_bytes_sent": 0,
                "total_bytes_received": 0,
                "total_bytes": 0,
                "avg_upload_speed_mbps": 0.0,
                "avg_download_speed_mbps": 0.0,
                "peak_upload_speed_mbps": 0.0,
                "peak_download_speed_mbps": 0.0,
                "first_recorded": None,
                "last_recorded": None,
            }

        return {
            "total_bytes_sent": int(row.total_sent or 0),
            "total_bytes_received": int(row.total_received or 0),
            "total_bytes": int((row.total_sent or 0) + (row.total_received or 0)),
            "avg_upload_speed_mbps": float(row.avg_upload or 0.0),
            "avg_download_speed_mbps": float(row.avg_download or 0.0),
            "peak_upload_speed_mbps": float(row.peak_upload or 0.0),
            "peak_download_speed_mbps": float(row.peak_download or 0.0),
            "first_recorded": row.first_recorded,
            "last_recorded": row.last_recorded,
        }

    async def delete_old_records(self, days: int = 30) -> int:
        """
        Delete bandwidth usage records older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        threshold = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(BandwidthUsage).where(BandwidthUsage.timestamp < threshold)
        )
        records = result.scalars().all()
        count = len(records)

        for record in records:
            await self.session.delete(record)

        await self.session.flush()
        return count
