"""Tests for notification handlers."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest

from src.models.alert import Alert, AlertRule, AlertSeverity, AlertStatus, NotificationChannel
from src.services.notification_handlers import (
    DiscordNotificationHandler,
    EmailNotificationHandler,
    NotificationManager,
    NotificationResult,
    SlackNotificationHandler,
    WebhookNotificationHandler,
    WebSocketNotificationHandler,
)


@pytest.fixture
def sample_alert():
    """Create sample alert for testing."""
    return Alert(
        id=1,
        rule_id=10,
        device_id="device-123",
        title="High Bandwidth Usage",
        message="Bandwidth exceeded threshold",
        severity=AlertSeverity.WARNING,
        status=AlertStatus.ACTIVE,
        metric_value=95.5,
        threshold_value=90.0,
        triggered_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_rule():
    """Create sample alert rule for testing."""
    rule = Mock(spec=AlertRule)
    rule.id = 10
    rule.name = "Test Rule"
    rule.notification_channels = []
    rule.notification_config = {}
    return rule


@pytest.mark.asyncio
class TestWebSocketNotificationHandler:
    """Tests for WebSocket notification handler."""

    async def test_send_success(self, sample_alert, sample_rule):
        """Test successful WebSocket notification."""
        mock_ws_manager = AsyncMock()
        handler = WebSocketNotificationHandler(mock_ws_manager)

        result = await handler.send(sample_alert, sample_rule)

        # Verify broadcast called with correct data
        mock_ws_manager.broadcast.assert_called_once()
        call_args = mock_ws_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "alert"
        assert call_args["data"]["id"] == 1
        assert call_args["data"]["title"] == "High Bandwidth Usage"
        assert call_args["data"]["severity"] == "warning"

        # Verify result
        assert result.success is True
        assert result.channel == "websocket"
        assert result.error is None

    async def test_send_with_broadcast_error(self, sample_alert, sample_rule):
        """Test WebSocket notification when broadcast fails."""
        mock_ws_manager = AsyncMock()
        mock_ws_manager.broadcast.side_effect = Exception("Connection error")
        handler = WebSocketNotificationHandler(mock_ws_manager)

        result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "websocket"
        assert "Connection error" in result.error


@pytest.mark.asyncio
class TestEmailNotificationHandler:
    """Tests for email notification handler."""

    async def test_send_success(self, sample_alert, sample_rule):
        """Test successful email notification."""
        smtp_config = {
            "host": "smtp.example.com",
            "port": 587,
            "username": "user@example.com",
            "password": "password",
            "from_address": "alerts@example.com",
            "use_tls": True,
        }
        sample_rule.notification_config = {"email_addresses": ["admin@example.com"]}

        handler = EmailNotificationHandler(smtp_config)

        with patch("src.services.notification_handlers.aiosmtplib.send", new_callable=AsyncMock):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is True
        assert result.channel == "email"
        assert result.details["recipients"] == ["admin@example.com"]
        assert "High Bandwidth Usage" in result.details["subject"]

    async def test_send_without_smtp_config(self, sample_alert, sample_rule):
        """Test email notification without SMTP configuration."""
        handler = EmailNotificationHandler({})

        result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "email"
        assert "SMTP not configured" in result.error

    async def test_send_without_email_addresses(self, sample_alert, sample_rule):
        """Test email notification without email addresses."""
        smtp_config = {"host": "smtp.example.com"}
        sample_rule.notification_config = {}

        handler = EmailNotificationHandler(smtp_config)

        result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "email"
        assert "No email addresses configured" in result.error

    async def test_send_with_custom_template(self, sample_alert, sample_rule):
        """Test email notification with custom template."""
        smtp_config = {
            "host": "smtp.example.com",
            "from_address": "alerts@example.com",
        }
        sample_rule.notification_config = {
            "email_addresses": ["admin@example.com"],
            "email_template": "Alert: {alert_title}\nSeverity: {severity}\n{alert_message}",
        }

        handler = EmailNotificationHandler(smtp_config)

        with patch("src.services.notification_handlers.aiosmtplib.send", new_callable=AsyncMock):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is True

    async def test_send_with_smtp_error(self, sample_alert, sample_rule):
        """Test email notification with SMTP error."""
        smtp_config = {"host": "smtp.example.com"}
        sample_rule.notification_config = {"email_addresses": ["admin@example.com"]}

        handler = EmailNotificationHandler(smtp_config)

        with patch(
            "src.services.notification_handlers.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=Exception("SMTP connection failed"),
        ):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "email"
        assert "SMTP connection failed" in result.error

    def test_format_email_default_template(self, sample_alert, sample_rule):
        """Test email formatting with default template."""
        handler = EmailNotificationHandler({})

        subject, body = handler._format_email(sample_alert, sample_rule)

        # Verify subject
        assert "[WARNING]" in subject
        assert "High Bandwidth Usage" in subject

        # Verify body
        assert "High Bandwidth Usage" in body
        assert "95.5" in body
        assert "90.0" in body

    def test_format_email_custom_template(self, sample_alert, sample_rule):
        """Test email formatting with custom template."""
        handler = EmailNotificationHandler({})
        template = "Alert: {alert_title}\nValue: {metric_value}"

        subject, body = handler._format_email(sample_alert, sample_rule, template)

        # Verify body uses template
        assert "Alert: High Bandwidth Usage" in body
        assert "Value: 95.5" in body

    def test_format_html_email(self, sample_alert, sample_rule):
        """Test HTML email formatting."""
        handler = EmailNotificationHandler({})

        html = handler._format_html_email(sample_alert, sample_rule)

        # Verify HTML contains alert data
        assert "High Bandwidth Usage" in html
        assert "WARNING" in html
        assert "95.5" in html
        assert "<!DOCTYPE html>" in html


@pytest.mark.asyncio
class TestSlackNotificationHandler:
    """Tests for Slack notification handler."""

    async def test_send_success(self, sample_alert, sample_rule):
        """Test successful Slack notification."""
        handler = SlackNotificationHandler("https://hooks.slack.com/services/TEST")

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is True
        assert result.channel == "slack"

    async def test_send_without_webhook_url(self, sample_alert, sample_rule):
        """Test Slack notification without webhook URL."""
        handler = SlackNotificationHandler(None)
        sample_rule.notification_config = {}

        result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "slack"
        assert "No Slack webhook URL configured" in result.error

    async def test_send_with_http_error(self, sample_alert, sample_rule):
        """Test Slack notification with HTTP error."""
        handler = SlackNotificationHandler("https://hooks.slack.com/services/TEST")

        # Mock HTTP error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Invalid payload"
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "slack"
        assert "HTTP 400" in result.error

    async def test_send_with_exception(self, sample_alert, sample_rule):
        """Test Slack notification with exception."""
        handler = SlackNotificationHandler("https://hooks.slack.com/services/TEST")

        with patch("aiohttp.ClientSession", side_effect=Exception("Connection failed")):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "slack"
        assert "Connection failed" in result.error


@pytest.mark.asyncio
class TestDiscordNotificationHandler:
    """Tests for Discord notification handler."""

    async def test_send_success(self, sample_alert, sample_rule):
        """Test successful Discord notification."""
        handler = DiscordNotificationHandler("https://discord.com/api/webhooks/TEST")

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is True
        assert result.channel == "discord"

    async def test_send_without_webhook_url(self, sample_alert, sample_rule):
        """Test Discord notification without webhook URL."""
        handler = DiscordNotificationHandler(None)
        sample_rule.notification_config = {}

        result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "discord"
        assert "No Discord webhook URL configured" in result.error

    async def test_send_with_http_error(self, sample_alert, sample_rule):
        """Test Discord notification with HTTP error."""
        handler = DiscordNotificationHandler("https://discord.com/api/webhooks/TEST")

        # Mock HTTP error response
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text.return_value = "Rate limited"
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "discord"
        assert "HTTP 429" in result.error


@pytest.mark.asyncio
class TestWebhookNotificationHandler:
    """Tests for webhook notification handler."""

    async def test_send_success(self, sample_alert, sample_rule):
        """Test successful webhook notification."""
        handler = WebhookNotificationHandler()
        sample_rule.notification_config = {"webhook_urls": ["https://example.com/webhook"]}

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is True
        assert result.channel == "webhook"

    async def test_send_without_webhook_urls(self, sample_alert, sample_rule):
        """Test webhook notification without URLs."""
        handler = WebhookNotificationHandler()
        sample_rule.notification_config = {}

        result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "webhook"
        assert "No webhook URLs configured" in result.error

    async def test_send_with_retries(self, sample_alert, sample_rule):
        """Test webhook notification with retries."""
        handler = WebhookNotificationHandler(max_retries=3)
        sample_rule.notification_config = {"webhook_urls": ["https://example.com/webhook"]}

        # Mock failing then succeeding responses
        mock_responses = [
            AsyncMock(status=500, __aenter__=AsyncMock(), __aexit__=AsyncMock()),
            AsyncMock(status=500, __aenter__=AsyncMock(), __aexit__=AsyncMock()),
            AsyncMock(status=200, __aenter__=AsyncMock(), __aexit__=AsyncMock()),
        ]

        for mock_response in mock_responses:
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.side_effect = [
            mock_responses[0],
            mock_responses[1],
            mock_responses[2],
        ]
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session), patch(
            "asyncio.sleep", new_callable=AsyncMock
        ):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result - should succeed on 3rd attempt
        assert result.success is True
        assert result.details["results"][0]["attempt"] == 3

    async def test_send_with_all_retries_failed(self, sample_alert, sample_rule):
        """Test webhook notification with all retries failed."""
        handler = WebhookNotificationHandler(max_retries=2)
        sample_rule.notification_config = {"webhook_urls": ["https://example.com/webhook"]}

        # Mock all failing responses
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session), patch(
            "asyncio.sleep", new_callable=AsyncMock
        ):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.channel == "webhook"
        assert result.details["results"][0]["success"] is False

    async def test_send_with_timeout(self, sample_alert, sample_rule):
        """Test webhook notification with timeout."""
        handler = WebhookNotificationHandler(timeout=1, max_retries=1)
        sample_rule.notification_config = {"webhook_urls": ["https://example.com/webhook"]}

        mock_session = AsyncMock()
        mock_session.post.side_effect = TimeoutError("Request timed out")
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify result
        assert result.success is False
        assert result.details["results"][0]["error"] == "Request timeout"

    async def test_send_multiple_webhooks(self, sample_alert, sample_rule):
        """Test sending to multiple webhook URLs."""
        handler = WebhookNotificationHandler()
        sample_rule.notification_config = {
            "webhook_urls": [
                "https://example.com/webhook1",
                "https://example.com/webhook2",
            ]
        }

        # Mock responses for both URLs
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await handler.send(sample_alert, sample_rule)

        # Verify both webhooks were sent
        assert result.success is True
        assert len(result.details["results"]) == 2
        assert all(r["success"] for r in result.details["results"])


@pytest.mark.asyncio
class TestNotificationManager:
    """Tests for notification manager."""

    async def test_send_notification_websocket(self, sample_alert, sample_rule):
        """Test sending notification via WebSocket."""
        mock_ws_manager = AsyncMock()
        manager = NotificationManager(websocket_manager=mock_ws_manager)

        result = await manager.send_notification(sample_alert, sample_rule, "websocket")

        # Verify result
        assert result.success is True
        assert result.channel == "websocket"

    async def test_send_notification_email(self, sample_alert, sample_rule):
        """Test sending notification via email."""
        smtp_config = {"host": "smtp.example.com"}
        sample_rule.notification_config = {"email_addresses": ["admin@example.com"]}

        manager = NotificationManager(smtp_config=smtp_config)

        with patch("src.services.notification_handlers.aiosmtplib.send", new_callable=AsyncMock):
            result = await manager.send_notification(sample_alert, sample_rule, "email")

        # Verify result
        assert result.success is True
        assert result.channel == "email"

    async def test_send_notification_invalid_channel(self, sample_alert, sample_rule):
        """Test sending notification with invalid channel."""
        manager = NotificationManager()

        # Remove the handler
        manager.handlers["invalid"] = None

        result = await manager.send_notification(sample_alert, sample_rule, "invalid")

        # Verify result
        assert result.success is False
        assert "Handler not available" in result.error

    async def test_send_all_notifications(self, sample_alert, sample_rule):
        """Test sending notifications to all configured channels."""
        mock_ws_manager = AsyncMock()
        manager = NotificationManager(websocket_manager=mock_ws_manager)

        # Configure rule with multiple channels
        sample_rule.notification_channels = [
            NotificationChannel.WEBSOCKET,
            NotificationChannel.EMAIL,
        ]
        sample_rule.notification_config = {"email_addresses": ["admin@example.com"]}

        # Mock email sending
        with patch("src.services.notification_handlers.aiosmtplib.send", new_callable=AsyncMock):
            results = await manager.send_all_notifications(sample_alert, sample_rule)

        # Verify results for all channels
        assert "websocket" in results
        assert "email" in results
        assert results["websocket"].success is True
        assert results["email"].success is True
