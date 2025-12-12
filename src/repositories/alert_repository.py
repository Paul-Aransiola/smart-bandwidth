"""
Repository for alert and alert rule data access.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert import Alert, AlertRule, AlertSeverity, AlertStatus
from src.repositories.base import BaseRepository


class AlertRuleRepository(BaseRepository[AlertRule]):
    """Repository for alert rule data access."""

    def __init__(self, session: AsyncSession):
        """Initialize alert rule repository."""
        super().__init__(session, AlertRule)

    async def get_enabled_rules(self) -> list[AlertRule]:
        """
        Get all enabled alert rules.

        Returns:
            List of enabled alert rules
        """
        result = await self.session.execute(
            select(AlertRule).where(AlertRule.is_enabled == True).order_by(AlertRule.id)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_rules_by_device(self, device_id: int) -> list[AlertRule]:
        """
        Get alert rules for a specific device.

        Args:
            device_id: Device ID

        Returns:
            List of alert rules for the device
        """
        result = await self.session.execute(
            select(AlertRule)
            .where(
                (AlertRule.device_id == device_id) | (AlertRule.device_id == None),  # noqa: E711
                AlertRule.is_enabled == True,  # noqa: E712
            )
            .order_by(AlertRule.id)
        )
        return list(result.scalars().all())

    async def get_rules_ready_to_trigger(self) -> list[AlertRule]:
        """
        Get rules that are ready to trigger (past cooldown period).

        Returns:
            List of rules ready to trigger
        """
        # Fetch all enabled rules and filter in Python since SQLite doesn't support interval arithmetic
        result = await self.session.execute(
            select(AlertRule).where(AlertRule.is_enabled == True)  # noqa: E712
        )
        all_rules = list(result.scalars().all())

        # Filter rules that are past cooldown period
        now = datetime.now()
        ready_rules = []
        for rule in all_rules:
            if rule.last_triggered_at is None:
                ready_rules.append(rule)
            else:
                cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
                if cooldown_end <= now:
                    ready_rules.append(rule)

        return ready_rules


class AlertRepository(BaseRepository[Alert]):
    """Repository for alert data access."""

    def __init__(self, session: AsyncSession):
        """Initialize alert repository."""
        super().__init__(session, Alert)

    async def get_by_status(
        self, status: AlertStatus, skip: int = 0, limit: int = 100
    ) -> list[Alert]:
        """
        Get alerts by status.

        Args:
            status: Alert status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of alerts with the specified status
        """
        result = await self.session.execute(
            select(Alert)
            .where(Alert.status == status)
            .order_by(Alert.triggered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_severity(
        self, severity: AlertSeverity, skip: int = 0, limit: int = 100
    ) -> list[Alert]:
        """
        Get alerts by severity.

        Args:
            severity: Alert severity
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of alerts with the specified severity
        """
        result = await self.session.execute(
            select(Alert)
            .where(Alert.severity == severity)
            .order_by(Alert.triggered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_rule(self, rule_id: int, skip: int = 0, limit: int = 100) -> list[Alert]:
        """
        Get alerts for a specific rule.

        Args:
            rule_id: Rule ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of alerts for the rule
        """
        result = await self.session.execute(
            select(Alert)
            .where(Alert.rule_id == rule_id)
            .order_by(Alert.triggered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_device(self, device_id: int, skip: int = 0, limit: int = 100) -> list[Alert]:
        """
        Get alerts for a specific device.

        Args:
            device_id: Device ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of alerts for the device
        """
        result = await self.session.execute(
            select(Alert)
            .where(Alert.device_id == device_id)
            .order_by(Alert.triggered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> list[Alert]:
        """
        Get alerts within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of alerts in the date range
        """
        result = await self.session.execute(
            select(Alert)
            .where(Alert.triggered_at >= start_date, Alert.triggered_at <= end_date)
            .order_by(Alert.triggered_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_alerts(self, skip: int = 0, limit: int = 100) -> list[Alert]:
        """
        Get active alerts.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of active alerts
        """
        return await self.get_by_status(AlertStatus.ACTIVE, skip, limit)

    async def get_recent_alerts(self, hours: int = 24, limit: int = 10) -> list[Alert]:
        """
        Get recent alerts.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of alerts

        Returns:
            List of recent alerts
        """
        threshold = datetime.now() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Alert)
            .where(Alert.triggered_at >= threshold)
            .order_by(Alert.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: AlertStatus) -> int:
        """
        Count alerts by status.

        Args:
            status: Alert status

        Returns:
            Number of alerts with the status
        """
        result = await self.session.execute(
            select(func.count(Alert.id)).where(Alert.status == status)
        )
        return result.scalar() or 0

    async def count_by_severity(self, severity: AlertSeverity) -> int:
        """
        Count alerts by severity.

        Args:
            severity: Alert severity

        Returns:
            Number of alerts with the severity
        """
        result = await self.session.execute(
            select(func.count(Alert.id)).where(Alert.severity == severity)
        )
        return result.scalar() or 0

    async def acknowledge_alert(self, alert_id: int) -> Alert | None:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Updated alert or None if not found
        """
        alert = await self.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        await self.session.flush()
        return alert

    async def resolve_alert(self, alert_id: int) -> Alert | None:
        """
        Resolve an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Updated alert or None if not found
        """
        alert = await self.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        await self.session.flush()
        return alert

    async def snooze_alert(self, alert_id: int, minutes: int) -> Alert | None:
        """
        Snooze an alert.

        Args:
            alert_id: Alert ID
            minutes: Minutes to snooze

        Returns:
            Updated alert or None if not found
        """
        alert = await self.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.SNOOZED
        alert.snoozed_until = datetime.now() + timedelta(minutes=minutes)
        await self.session.flush()
        return alert

    async def get_alert_statistics(self) -> dict:
        """
        Get alert statistics.

        Returns:
            Dictionary with alert statistics
        """
        total = await self.session.execute(select(func.count(Alert.id)))
        active = await self.count_by_status(AlertStatus.ACTIVE)
        acknowledged = await self.count_by_status(AlertStatus.ACKNOWLEDGED)
        resolved = await self.count_by_status(AlertStatus.RESOLVED)
        critical = await self.count_by_severity(AlertSeverity.CRITICAL)

        # Count by severity
        severity_counts = {}
        for severity in AlertSeverity:
            count = await self.count_by_severity(severity)
            severity_counts[severity.value] = count

        # Count by status
        status_counts = {}
        for status in AlertStatus:
            count = await self.count_by_status(status)
            status_counts[status.value] = count

        return {
            "total_alerts": total.scalar() or 0,
            "active_alerts": active,
            "acknowledged_alerts": acknowledged,
            "resolved_alerts": resolved,
            "critical_alerts": critical,
            "by_severity": severity_counts,
            "by_status": status_counts,
        }
