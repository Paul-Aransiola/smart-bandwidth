"""
Alert service for evaluating rules and managing alerts.
"""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert import (
    Alert,
    AlertCondition,
    AlertMetric,
    AlertRule,
    AlertStatus,
)
from src.models.device import Device
from src.repositories.alert_repository import AlertRepository, AlertRuleRepository
from src.repositories.bandwidth_repository import BandwidthUsageRepository
from src.repositories.device_repository import DeviceRepository
from src.services.notification_handlers import NotificationManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertService:
    """Service for alert evaluation and management."""

    def __init__(
        self,
        session: AsyncSession,
        alert_repo: AlertRepository | None = None,
        rule_repo: AlertRuleRepository | None = None,
        device_repo: DeviceRepository | None = None,
        bandwidth_repo: BandwidthUsageRepository | None = None,
        notification_manager: NotificationManager | None = None,
    ):
        """
        Initialize alert service.

        Args:
            session: Database session
            alert_repo: Alert repository (created if None)
            rule_repo: Alert rule repository (created if None)
            device_repo: Device repository (created if None)
            bandwidth_repo: Bandwidth repository (created if None)
            notification_manager: Notification manager (created if None)
        """
        self.session = session
        self.alert_repo = alert_repo or AlertRepository(session)
        self.rule_repo = rule_repo or AlertRuleRepository(session)
        self.device_repo = device_repo or DeviceRepository(session)
        self.bandwidth_repo = bandwidth_repo or BandwidthUsageRepository(session)
        self.notification_manager = notification_manager or NotificationManager()

    async def evaluate_all_rules(self) -> dict[str, int]:
        """
        Evaluate all enabled alert rules.

        Returns:
            Dictionary with counts: rules_checked, alerts_triggered
        """
        logger.info("Starting alert rule evaluation")

        # Get all enabled rules ready to trigger
        rules = await self.rule_repo.get_rules_ready_to_trigger()
        rules_checked = len(rules)

        if not rules:
            logger.debug("No enabled rules ready to trigger")
            return {"rules_checked": 0, "alerts_triggered": 0}

        logger.info(f"Evaluating {rules_checked} alert rules")

        # Evaluate each rule
        alerts_triggered = 0
        for rule in rules:
            try:
                triggered = await self._evaluate_rule(rule)
                if triggered:
                    alerts_triggered += 1
            except Exception as e:
                logger.error(
                    f"Error evaluating rule {rule.id} ({rule.name}): {e}",
                    exc_info=True,
                )

        logger.info(
            f"Alert evaluation complete: {rules_checked} rules checked, "
            f"{alerts_triggered} alerts triggered"
        )

        return {
            "rules_checked": rules_checked,
            "alerts_triggered": alerts_triggered,
        }

    async def _evaluate_rule(self, rule: AlertRule) -> bool:
        """
        Evaluate a single alert rule.

        Args:
            rule: Alert rule to evaluate

        Returns:
            True if alert was triggered, False otherwise
        """
        logger.debug(f"Evaluating rule: {rule.name} (ID: {rule.id})")

        # Get devices to check
        if rule.device_id:
            devices = [await self.device_repo.get(rule.device_id)]
            if not devices[0]:
                logger.warning(f"Device {rule.device_id} not found for rule {rule.id}")
                return False
        else:
            # Global rule - check all active devices
            devices = await self.device_repo.get_all_active()

        if not devices:
            logger.debug(f"No devices to check for rule {rule.id}")
            return False

        # Check each device
        triggered = False
        for device in devices:
            if await self._check_device_against_rule(device, rule):
                triggered = True

        return triggered

    async def _check_device_against_rule(self, device: Device, rule: AlertRule) -> bool:
        """
        Check if a device triggers an alert rule.

        Args:
            device: Device to check
            rule: Alert rule

        Returns:
            True if alert was triggered, False otherwise
        """
        # Get metric value
        metric_value = await self._get_metric_value(device, rule.metric, rule.time_window_minutes)

        if metric_value is None:
            logger.debug(f"No metric value for device {device.id}, metric {rule.metric}")
            return False

        # Check threshold condition
        threshold_met = self._check_threshold(metric_value, rule.condition, rule.threshold_value)

        if not threshold_met:
            return False

        # Threshold met - create alert
        logger.info(
            f"Alert triggered: {rule.name} for device {device.hostname} "
            f"(metric={metric_value}, threshold={rule.threshold_value})"
        )

        await self._create_alert(device, rule, metric_value)

        # Update rule last triggered time
        rule.last_triggered_at = datetime.utcnow()
        await self.rule_repo.update(rule.id, {"last_triggered_at": rule.last_triggered_at})

        return True

    async def _get_metric_value(
        self, device: Device, metric: AlertMetric, time_window_minutes: int
    ) -> float | None:
        """
        Get current metric value for a device.

        Args:
            device: Device to check
            metric: Metric to retrieve
            time_window_minutes: Time window for aggregation

        Returns:
            Metric value or None if unavailable
        """
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=time_window_minutes)

        if metric == AlertMetric.BANDWIDTH_USAGE:
            # Get average bandwidth usage in time window (Mbps)
            usage_records = await self.bandwidth_repo.get_by_time_range(device.id, start_time, now)
            if not usage_records:
                return None

            # Calculate average bandwidth (convert bytes to Mbps)
            total_bytes = sum(r.bytes_received + r.bytes_transmitted for r in usage_records)
            time_span_seconds = time_window_minutes * 60
            mbps = (total_bytes * 8) / (time_span_seconds * 1_000_000)
            return round(mbps, 2)

        elif metric == AlertMetric.UPLOAD_SPEED:
            # Get average upload speed in time window (Mbps)
            usage_records = await self.bandwidth_repo.get_by_time_range(device.id, start_time, now)
            if not usage_records:
                return None

            total_bytes = sum(r.bytes_transmitted for r in usage_records)
            time_span_seconds = time_window_minutes * 60
            mbps = (total_bytes * 8) / (time_span_seconds * 1_000_000)
            return round(mbps, 2)

        elif metric == AlertMetric.DOWNLOAD_SPEED:
            # Get average download speed in time window (Mbps)
            usage_records = await self.bandwidth_repo.get_by_time_range(device.id, start_time, now)
            if not usage_records:
                return None

            total_bytes = sum(r.bytes_received for r in usage_records)
            time_span_seconds = time_window_minutes * 60
            mbps = (total_bytes * 8) / (time_span_seconds * 1_000_000)
            return round(mbps, 2)

        elif metric == AlertMetric.TOTAL_BYTES:
            # Get total bytes in time window
            usage_records = await self.bandwidth_repo.get_by_time_range(device.id, start_time, now)
            if not usage_records:
                return None

            total_bytes = sum(r.bytes_received + r.bytes_transmitted for r in usage_records)
            return float(total_bytes)

        elif metric == AlertMetric.DEVICE_COUNT:
            # Get active device count (not device-specific)
            devices = await self.device_repo.get_all_active()
            return float(len(devices))

        return None

    def _check_threshold(
        self, metric_value: float, condition: AlertCondition, threshold: float
    ) -> bool:
        """
        Check if metric value meets threshold condition.

        Args:
            metric_value: Current metric value
            condition: Condition to check
            threshold: Threshold value

        Returns:
            True if condition is met, False otherwise
        """
        if condition == AlertCondition.GREATER_THAN:
            return metric_value > threshold
        elif condition == AlertCondition.LESS_THAN:
            return metric_value < threshold
        elif condition == AlertCondition.EQUALS:
            return abs(metric_value - threshold) < 0.01  # Float comparison tolerance
        elif condition == AlertCondition.NOT_EQUALS:
            return abs(metric_value - threshold) >= 0.01
        return False

    async def _create_alert(self, device: Device, rule: AlertRule, metric_value: float) -> Alert:
        """
        Create a new alert.

        Args:
            device: Device that triggered the alert
            rule: Alert rule that was triggered
            metric_value: Current metric value

        Returns:
            Created alert
        """
        # Generate alert message
        message = self._generate_alert_message(device, rule, metric_value)

        # Create alert
        alert = await self.alert_repo.create(
            {
                "rule_id": rule.id,
                "device_id": device.id,
                "title": rule.name,
                "message": message,
                "severity": rule.severity,
                "status": AlertStatus.ACTIVE,
                "metric_value": metric_value,
                "threshold_value": rule.threshold_value,
                "triggered_at": datetime.utcnow(),
                "notifications_sent": {},
            }
        )

        # Schedule notifications (non-blocking)
        asyncio.create_task(self._send_notifications(alert, rule))

        return alert

    def _generate_alert_message(self, device: Device, rule: AlertRule, metric_value: float) -> str:
        """
        Generate human-readable alert message.

        Args:
            device: Device that triggered alert
            rule: Alert rule
            metric_value: Current metric value

        Returns:
            Alert message
        """
        metric_name = rule.metric.value.replace("_", " ").title()
        condition_text = {
            AlertCondition.GREATER_THAN: "exceeded",
            AlertCondition.LESS_THAN: "dropped below",
            AlertCondition.EQUALS: "equals",
            AlertCondition.NOT_EQUALS: "does not equal",
        }.get(rule.condition, "met condition for")

        # Format metric value based on type
        if rule.metric in [
            AlertMetric.BANDWIDTH_USAGE,
            AlertMetric.UPLOAD_SPEED,
            AlertMetric.DOWNLOAD_SPEED,
        ]:
            value_str = f"{metric_value:.2f} Mbps"
            threshold_str = f"{rule.threshold_value:.2f} Mbps"
        elif rule.metric == AlertMetric.TOTAL_BYTES:
            value_str = f"{metric_value / 1_000_000:.2f} MB"
            threshold_str = f"{rule.threshold_value / 1_000_000:.2f} MB"
        else:
            value_str = str(int(metric_value))
            threshold_str = str(int(rule.threshold_value))

        message = (
            f"Device '{device.hostname}' ({device.ip_address}): "
            f"{metric_name} {condition_text} threshold. "
            f"Current: {value_str}, Threshold: {threshold_str}"
        )

        if rule.time_window_minutes > 0:
            message += f" (over {rule.time_window_minutes} minutes)"

        return message

    async def _send_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """
        Send notifications for an alert.

        Args:
            alert: Alert to notify about
            rule: Alert rule with notification configuration
        """
        # Send notifications via NotificationManager
        results = await self.notification_manager.send_all_notifications(alert, rule)

        # Convert results to JSON-serializable format
        notifications_sent = {}
        for channel, result in results.items():
            notifications_sent[channel] = {
                "sent_at": result.timestamp.isoformat(),
                "success": result.success,
                "error": result.error,
                "details": result.details,
            }

        # Update alert with notification status
        await self.alert_repo.update(alert.id, {"notifications_sent": notifications_sent})

    async def test_rule(self, rule_id: int) -> dict:
        """
        Test an alert rule without triggering actual alerts.

        Args:
            rule_id: Rule ID to test

        Returns:
            Test results with devices checked and threshold status
        """
        rule = await self.rule_repo.get(rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        # Get devices to check
        if rule.device_id:
            devices = [await self.device_repo.get(rule.device_id)]
            if not devices[0]:
                return {"error": f"Device {rule.device_id} not found"}
        else:
            devices = await self.device_repo.get_all_active()

        results = []
        for device in devices:
            metric_value = await self._get_metric_value(
                device, rule.metric, rule.time_window_minutes
            )

            if metric_value is None:
                results.append(
                    {
                        "device_id": device.id,
                        "device_hostname": device.hostname,
                        "metric_value": None,
                        "threshold_met": False,
                        "message": "No data available",
                    }
                )
                continue

            threshold_met = self._check_threshold(
                metric_value, rule.condition, rule.threshold_value
            )

            results.append(
                {
                    "device_id": device.id,
                    "device_hostname": device.hostname,
                    "metric_value": metric_value,
                    "threshold_value": rule.threshold_value,
                    "condition": rule.condition.value,
                    "threshold_met": threshold_met,
                    "message": self._generate_alert_message(device, rule, metric_value)
                    if threshold_met
                    else "Threshold not met",
                }
            )

        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "devices_checked": len(devices),
            "results": results,
        }
