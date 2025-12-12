"""
Repositories for advanced bandwidth control features.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.advanced_controls import BandwidthQuota, QoSPolicy, ThrottleSchedule
from src.models.settings import GlobalSettings
from src.repositories.base import BaseRepository


class BandwidthQuotaRepository(BaseRepository[BandwidthQuota]):
    """Repository for bandwidth quota data access."""

    def __init__(self, session: AsyncSession):
        """Initialize bandwidth quota repository."""
        super().__init__(session, BandwidthQuota)

    async def get_by_device(self, device_id: int) -> list[BandwidthQuota]:
        """
        Get all quotas for a device.

        Args:
            device_id: Device ID

        Returns:
            List of bandwidth quotas
        """
        result = await self.session.execute(
            select(BandwidthQuota).where(BandwidthQuota.device_id == device_id)
        )
        return list(result.scalars().all())

    async def get_active_quotas(self, device_id: int | None = None) -> list[BandwidthQuota]:
        """
        Get active quotas, optionally filtered by device.

        Args:
            device_id: Optional device ID filter

        Returns:
            List of active bandwidth quotas
        """
        query = select(BandwidthQuota).where(BandwidthQuota.is_active == True)  # noqa: E712

        if device_id is not None:
            query = query.where(BandwidthQuota.device_id == device_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_quotas_near_limit(self, threshold_percent: float = 80.0) -> list[BandwidthQuota]:
        """
        Get quotas that are near their limit.

        Args:
            threshold_percent: Usage percentage threshold

        Returns:
            List of quotas near limit
        """
        result = await self.session.execute(
            select(BandwidthQuota).where(
                BandwidthQuota.is_active == True  # noqa: E712
            )
        )
        quotas = list(result.scalars().all())

        # Filter by usage percentage
        return [q for q in quotas if q.usage_percent >= threshold_percent]

    async def reset_quota(self, quota_id: int) -> BandwidthQuota | None:
        """
        Reset a quota's used bytes.

        Args:
            quota_id: Quota ID

        Returns:
            Updated quota or None
        """
        quota = await self.get_by_id(quota_id)
        if not quota:
            return None

        quota.used_bytes = 0
        quota.last_reset_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(quota)

        return quota


class QoSPolicyRepository(BaseRepository[QoSPolicy]):
    """Repository for QoS policy data access."""

    def __init__(self, session: AsyncSession):
        """Initialize QoS policy repository."""
        super().__init__(session, QoSPolicy)

    async def get_by_device(self, device_id: int) -> list[QoSPolicy]:
        """
        Get all QoS policies for a device.

        Args:
            device_id: Device ID

        Returns:
            List of QoS policies
        """
        result = await self.session.execute(
            select(QoSPolicy).where(QoSPolicy.device_id == device_id)
        )
        return list(result.scalars().all())

    async def get_by_priority(self, priority: str) -> list[QoSPolicy]:
        """
        Get policies by priority level.

        Args:
            priority: Priority level

        Returns:
            List of QoS policies
        """
        result = await self.session.execute(
            select(QoSPolicy).where(
                QoSPolicy.priority == priority,
                QoSPolicy.is_enabled == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_enabled_policies(self) -> list[QoSPolicy]:
        """
        Get all enabled QoS policies.

        Returns:
            List of enabled policies
        """
        result = await self.session.execute(
            select(QoSPolicy).where(QoSPolicy.is_enabled == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_name(self, policy_name: str) -> QoSPolicy | None:
        """
        Get policy by name.

        Args:
            policy_name: Policy name

        Returns:
            QoS policy or None
        """
        result = await self.session.execute(
            select(QoSPolicy).where(QoSPolicy.policy_name == policy_name)
        )
        return result.scalar_one_or_none()


class ThrottleScheduleRepository(BaseRepository[ThrottleSchedule]):
    """Repository for throttle schedule data access."""

    def __init__(self, session: AsyncSession):
        """Initialize throttle schedule repository."""
        super().__init__(session, ThrottleSchedule)

    async def get_by_device(self, device_id: int) -> list[ThrottleSchedule]:
        """
        Get all schedules for a device.

        Args:
            device_id: Device ID

        Returns:
            List of throttle schedules
        """
        result = await self.session.execute(
            select(ThrottleSchedule).where(ThrottleSchedule.device_id == device_id)
        )
        return list(result.scalars().all())

    async def get_enabled_schedules(self) -> list[ThrottleSchedule]:
        """
        Get all enabled schedules.

        Returns:
            List of enabled schedules
        """
        result = await self.session.execute(
            select(ThrottleSchedule).where(ThrottleSchedule.is_enabled == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_active_schedules(self, current_time: datetime) -> list[ThrottleSchedule]:
        """
        Get schedules that should be active at the given time.

        Args:
            current_time: Current datetime

        Returns:
            List of active schedules
        """
        schedules = await self.get_enabled_schedules()

        # Filter by time and date range
        active = []
        current_time_only = current_time.time()
        current_day = current_time.weekday()

        for schedule in schedules:
            # Check time range
            if schedule.start_time <= current_time_only <= schedule.end_time:
                # Check date range if specified
                if schedule.start_date and current_time < schedule.start_date:
                    continue
                if schedule.end_date and current_time > schedule.end_date:
                    continue

                # Check day of week for weekly recurrence
                if schedule.recurrence == "weekly" and schedule.days_of_week:
                    days = [int(d) for d in schedule.days_of_week.split(",")]
                    if current_day not in days:
                        continue

                active.append(schedule)

        return active

    async def update_last_executed(self, schedule_id: int) -> ThrottleSchedule | None:
        """
        Update last executed timestamp.

        Args:
            schedule_id: Schedule ID

        Returns:
            Updated schedule or None
        """
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        schedule.last_executed_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(schedule)

        return schedule


class GlobalSettingsRepository(BaseRepository[GlobalSettings]):
    """Repository for global settings data access."""

    def __init__(self, session: AsyncSession):
        """Initialize global settings repository."""
        super().__init__(session, GlobalSettings)

    async def get_by_key(self, key: str) -> GlobalSettings | None:
        """
        Get setting by key.

        Args:
            key: Setting key

        Returns:
            GlobalSettings instance or None
        """
        result = await self.session.execute(
            select(GlobalSettings).where(GlobalSettings.setting_key == key)
        )
        return result.scalar_one_or_none()

    async def get_value(self, key: str, default: str | None = None) -> str | None:
        """
        Get setting value by key.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        setting = await self.get_by_key(key)
        return setting.setting_value if setting else default

    async def set_value(
        self, key: str, value: str, setting_type: str = "string", description: str | None = None
    ) -> GlobalSettings:
        """
        Set or update a setting value.

        Args:
            key: Setting key
            value: Setting value
            setting_type: Type of the setting
            description: Description of the setting

        Returns:
            Updated or created GlobalSettings instance
        """
        existing = await self.get_by_key(key)

        if existing:
            existing.setting_value = value
            existing.setting_type = setting_type
            if description:
                existing.description = description
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            new_setting = GlobalSettings(
                setting_key=key,
                setting_value=value,
                setting_type=setting_type,
                description=description,
            )
            self.session.add(new_setting)
            await self.session.commit()
            await self.session.refresh(new_setting)
            return new_setting

    async def delete_by_key(self, key: str) -> bool:
        """
        Delete a setting by key.

        Args:
            key: Setting key

        Returns:
            True if deleted, False if not found
        """
        setting = await self.get_by_key(key)
        if setting:
            await self.session.delete(setting)
            await self.session.commit()
            return True
        return False
