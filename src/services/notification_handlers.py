"""
Notification handlers for alert delivery.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

from src.models.alert import Alert, AlertRule
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification attempt."""

    success: bool
    channel: str
    timestamp: datetime
    error: str | None = None
    details: dict[str, Any] | None = None


class NotificationHandler(ABC):
    """Base class for notification handlers."""

    @abstractmethod
    async def send(self, alert: Alert, rule: AlertRule) -> NotificationResult:
        """
        Send notification for an alert.

        Args:
            alert: Alert to notify about
            rule: Alert rule with notification configuration

        Returns:
            Notification result
        """
        pass


class WebSocketNotificationHandler(NotificationHandler):
    """WebSocket notification handler."""

    def __init__(self, websocket_manager):
        """
        Initialize WebSocket handler.

        Args:
            websocket_manager: WebSocket connection manager
        """
        self.ws_manager = websocket_manager

    async def send(self, alert: Alert, rule: AlertRule) -> NotificationResult:
        """Send alert via WebSocket broadcast."""
        try:
            # Broadcast alert to all connected clients
            await self.ws_manager.broadcast(
                {
                    "type": "alert",
                    "data": {
                        "id": alert.id,
                        "rule_id": alert.rule_id,
                        "device_id": alert.device_id,
                        "title": alert.title,
                        "message": alert.message,
                        "severity": alert.severity.value,
                        "status": alert.status.value,
                        "metric_value": alert.metric_value,
                        "threshold_value": alert.threshold_value,
                        "triggered_at": alert.triggered_at.isoformat(),
                    },
                }
            )

            logger.info(f"WebSocket notification sent for alert {alert.id}")

            return NotificationResult(
                success=True,
                channel="websocket",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"WebSocket notification failed for alert {alert.id}: {e}")
            return NotificationResult(
                success=False,
                channel="websocket",
                timestamp=datetime.utcnow(),
                error=str(e),
            )


class EmailNotificationHandler(NotificationHandler):
    """Email notification handler."""

    def __init__(self, smtp_config: dict[str, Any] | None = None):
        """
        Initialize email handler.

        Args:
            smtp_config: SMTP configuration (host, port, username, password, from_address)
        """
        self.smtp_config = smtp_config or {}

    async def send(self, alert: Alert, rule: AlertRule) -> NotificationResult:
        """Send alert via email."""
        try:
            # Get email configuration from rule
            notification_config = rule.notification_config or {}
            email_addresses = notification_config.get("email_addresses", [])

            if not email_addresses:
                logger.warning(f"No email addresses configured for rule {rule.id}")
                return NotificationResult(
                    success=False,
                    channel="email",
                    timestamp=datetime.utcnow(),
                    error="No email addresses configured",
                )

            # Get email template
            email_template = notification_config.get("email_template")
            subject, body = self._format_email(alert, rule, email_template)

            # TODO: Implement actual email sending with aiosmtplib
            # For now, just log what would be sent
            logger.info(
                f"Email notification for alert {alert.id}: "
                f"to={email_addresses}, subject={subject}"
            )

            # Placeholder implementation
            logger.warning("Email sending not yet implemented - would send to: " + ", ".join(email_addresses))

            return NotificationResult(
                success=False,
                channel="email",
                timestamp=datetime.utcnow(),
                error="Email handler not yet implemented",
                details={
                    "recipients": email_addresses,
                    "subject": subject,
                },
            )

        except Exception as e:
            logger.error(f"Email notification failed for alert {alert.id}: {e}")
            return NotificationResult(
                success=False,
                channel="email",
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    def _format_email(
        self, alert: Alert, rule: AlertRule, template: str | None = None
    ) -> tuple[str, str]:
        """
        Format email subject and body.

        Args:
            alert: Alert data
            rule: Alert rule
            template: Custom email template

        Returns:
            Tuple of (subject, body)
        """
        # Subject
        subject = f"[{alert.severity.value.upper()}] {alert.title}"

        # Body
        if template:
            # Use custom template with variable substitution
            body = template.format(
                alert_title=alert.title,
                alert_message=alert.message,
                severity=alert.severity.value,
                device_id=alert.device_id,
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                triggered_at=alert.triggered_at.isoformat(),
            )
        else:
            # Default template
            body = f"""
Alert Notification

Title: {alert.title}
Severity: {alert.severity.value.upper()}
Status: {alert.status.value}

{alert.message}

Details:
- Metric Value: {alert.metric_value}
- Threshold Value: {alert.threshold_value}
- Triggered At: {alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
- Alert ID: {alert.id}
- Rule ID: {alert.rule_id}
- Device ID: {alert.device_id}

This is an automated alert from the Smart Bandwidth Monitor.
"""

        return subject, body.strip()


class WebhookNotificationHandler(NotificationHandler):
    """Webhook notification handler."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize webhook handler.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def send(self, alert: Alert, rule: AlertRule) -> NotificationResult:
        """Send alert via webhook."""
        try:
            # Get webhook URLs from rule configuration
            notification_config = rule.notification_config or {}
            webhook_urls = notification_config.get("webhook_urls", [])

            if not webhook_urls:
                logger.warning(f"No webhook URLs configured for rule {rule.id}")
                return NotificationResult(
                    success=False,
                    channel="webhook",
                    timestamp=datetime.utcnow(),
                    error="No webhook URLs configured",
                )

            # Prepare webhook payload
            payload = {
                "alert_id": alert.id,
                "rule_id": alert.rule_id,
                "rule_name": rule.name,
                "device_id": alert.device_id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "metric_value": alert.metric_value,
                "threshold_value": alert.threshold_value,
                "triggered_at": alert.triggered_at.isoformat(),
            }

            # Send to all webhook URLs
            results = []
            async with aiohttp.ClientSession() as session:
                for url in webhook_urls:
                    result = await self._send_webhook(session, url, payload)
                    results.append(result)

            # Check if all succeeded
            all_success = all(r["success"] for r in results)

            logger.info(
                f"Webhook notifications for alert {alert.id}: "
                f"{sum(r['success'] for r in results)}/{len(results)} succeeded"
            )

            return NotificationResult(
                success=all_success,
                channel="webhook",
                timestamp=datetime.utcnow(),
                error=None if all_success else "Some webhooks failed",
                details={"results": results},
            )

        except Exception as e:
            logger.error(f"Webhook notification failed for alert {alert.id}: {e}")
            return NotificationResult(
                success=False,
                channel="webhook",
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    async def _send_webhook(
        self, session: aiohttp.ClientSession, url: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Send webhook to a single URL with retries.

        Args:
            session: HTTP session
            url: Webhook URL
            payload: JSON payload

        Returns:
            Result dictionary
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status < 400:
                        logger.debug(f"Webhook sent to {url}: {response.status}")
                        return {
                            "url": url,
                            "success": True,
                            "status_code": response.status,
                            "attempt": attempt,
                        }
                    else:
                        last_error = f"HTTP {response.status}"
                        logger.warning(
                            f"Webhook to {url} failed with status {response.status} "
                            f"(attempt {attempt}/{self.max_retries})"
                        )

            except TimeoutError:
                last_error = "Request timeout"
                logger.warning(
                    f"Webhook to {url} timed out (attempt {attempt}/{self.max_retries})"
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Webhook to {url} failed: {e} (attempt {attempt}/{self.max_retries})"
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                await asyncio.sleep(2**attempt)

        # All retries failed
        logger.error(f"Webhook to {url} failed after {self.max_retries} attempts")
        return {
            "url": url,
            "success": False,
            "error": last_error,
            "attempts": self.max_retries,
        }


class NotificationManager:
    """Manager for coordinating notifications across multiple channels."""

    def __init__(
        self,
        websocket_manager=None,
        smtp_config: dict[str, Any] | None = None,
        webhook_timeout: int = 30,
        webhook_retries: int = 3,
    ):
        """
        Initialize notification manager.

        Args:
            websocket_manager: WebSocket connection manager
            smtp_config: SMTP configuration for email
            webhook_timeout: Webhook request timeout
            webhook_retries: Webhook retry attempts
        """
        self.handlers = {
            "websocket": WebSocketNotificationHandler(websocket_manager)
            if websocket_manager
            else None,
            "email": EmailNotificationHandler(smtp_config),
            "webhook": WebhookNotificationHandler(webhook_timeout, webhook_retries),
        }

    async def send_notification(
        self, alert: Alert, rule: AlertRule, channel: str
    ) -> NotificationResult:
        """
        Send notification via specified channel.

        Args:
            alert: Alert to notify about
            rule: Alert rule
            channel: Notification channel

        Returns:
            Notification result
        """
        handler = self.handlers.get(channel)

        if not handler:
            logger.error(f"No handler available for channel: {channel}")
            return NotificationResult(
                success=False,
                channel=channel,
                timestamp=datetime.utcnow(),
                error=f"Handler not available for channel: {channel}",
            )

        return await handler.send(alert, rule)

    async def send_all_notifications(
        self, alert: Alert, rule: AlertRule
    ) -> dict[str, NotificationResult]:
        """
        Send notifications via all configured channels.

        Args:
            alert: Alert to notify about
            rule: Alert rule with channel configuration

        Returns:
            Dictionary mapping channel names to results
        """
        results = {}

        # Send to each configured channel
        for channel in rule.notification_channels:
            channel_name = channel.value
            result = await self.send_notification(alert, rule, channel_name)
            results[channel_name] = result

        return results
