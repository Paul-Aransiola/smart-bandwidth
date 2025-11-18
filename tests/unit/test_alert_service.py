"""
Unit tests for AlertService.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.alert import (
    Alert,
    AlertCondition,
    AlertMetric,
    AlertRule,
    AlertSeverity,
    AlertStatus,
)
from src.models.device import Device, DeviceStatus
from src.services.alert_service import AlertService


@pytest.fixture
def sample_device():
    """Create sample device for testing."""
    return Device(
        id=1,
        ip_address="192.168.1.100",
        mac_address="00:11:22:33:44:55",
        hostname="test-device",
        device_name="Test Device",
        status=DeviceStatus.ACTIVE,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        is_blocked=False,
        is_throttled=False,
        total_bytes_sent=0,
        total_bytes_received=0,
    )


@pytest.fixture
def sample_bandwidth_rule():
    """Create sample bandwidth alert rule."""
    return AlertRule(
        id=1,
        name="High Bandwidth Usage",
        description="Alert when bandwidth exceeds threshold",
        metric=AlertMetric.BANDWIDTH_USAGE,
        condition=AlertCondition.GREATER_THAN,
        threshold_value=100.0,  # 100 Mbps
        time_window_minutes=5,
        severity=AlertSeverity.WARNING,
        is_enabled=True,
        device_id=None,  # Global rule
        cooldown_minutes=15,
        notification_channels=["email", "slack"],
        last_triggered_at=None,
    )


@pytest.fixture
def sample_device_rule(sample_device):
    """Create sample device-specific alert rule."""
    return AlertRule(
        id=2,
        name="Device Offline",
        description="Alert when device goes offline",
        metric=AlertMetric.DEVICE_COUNT,
        condition=AlertCondition.LESS_THAN,
        threshold_value=1.0,
        time_window_minutes=0,
        severity=AlertSeverity.CRITICAL,
        is_enabled=True,
        device_id=sample_device.id,
        cooldown_minutes=10,
        notification_channels=["email"],
        last_triggered_at=None,
    )


@pytest.fixture
def mock_alert_repo():
    """Create mock alert repository."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_rule_repo():
    """Create mock alert rule repository."""
    repo = MagicMock()
    repo.get_rules_ready_to_trigger = AsyncMock()
    repo.update = AsyncMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_device_repo():
    """Create mock device repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_all_active = AsyncMock()
    return repo


@pytest.fixture
def mock_bandwidth_repo():
    """Create mock bandwidth repository."""
    repo = MagicMock()
    repo.get_by_time_range = AsyncMock()
    return repo


@pytest.fixture
def mock_notification_manager():
    """Create mock notification manager."""
    manager = MagicMock()
    manager.send_all_notifications = AsyncMock()
    return manager


@pytest.fixture
def alert_service(
    db_session,
    mock_alert_repo,
    mock_rule_repo,
    mock_device_repo,
    mock_bandwidth_repo,
    mock_notification_manager,
):
    """Create alert service with mocked dependencies."""
    return AlertService(
        session=db_session,
        alert_repo=mock_alert_repo,
        rule_repo=mock_rule_repo,
        device_repo=mock_device_repo,
        bandwidth_repo=mock_bandwidth_repo,
        notification_manager=mock_notification_manager,
    )


@pytest.mark.asyncio
class TestAlertServiceEvaluation:
    """Tests for alert rule evaluation."""

    async def test_evaluate_all_rules_no_rules(self, alert_service, mock_rule_repo):
        """Test evaluation when no rules are ready to trigger."""
        mock_rule_repo.get_rules_ready_to_trigger.return_value = []

        result = await alert_service.evaluate_all_rules()

        assert result["rules_checked"] == 0
        assert result["alerts_triggered"] == 0

    async def test_evaluate_all_rules_success(
        self,
        alert_service,
        mock_rule_repo,
        mock_device_repo,
        mock_bandwidth_repo,
        mock_alert_repo,
        sample_device,
        sample_bandwidth_rule,
    ):
        """Test successful rule evaluation with alert triggered."""
        # Setup mocks
        mock_rule_repo.get_rules_ready_to_trigger.return_value = [sample_bandwidth_rule]
        mock_device_repo.get_all_active.return_value = [sample_device]

        # Mock bandwidth data that exceeds threshold (100 Mbps)
        # Formula: (total_bytes * 8) / (time_window_minutes * 60 * 1_000_000)
        # We need: (bytes * 8) / (5 * 60 * 1_000_000) > 100
        # So: bytes > (100 * 5 * 60 * 1_000_000) / 8 = 3,750,000,000
        bandwidth_record = MagicMock()
        bandwidth_record.bytes_received = 2_000_000_000  # 2 GB
        bandwidth_record.bytes_transmitted = 2_000_000_000  # 2 GB
        mock_bandwidth_repo.get_by_time_range.return_value = [bandwidth_record]

        # Mock alert creation
        created_alert = Alert(
            id=1,
            rule_id=sample_bandwidth_rule.id,
            device_id=sample_device.id,
            title=sample_bandwidth_rule.name,
            message="Test alert",
            severity=sample_bandwidth_rule.severity,
            status=AlertStatus.ACTIVE,
            metric_value=213.33,
            threshold_value=100.0,
            triggered_at=datetime.utcnow(),
            notifications_sent={},
        )
        mock_alert_repo.create.return_value = created_alert

        with patch("asyncio.create_task"):
            result = await alert_service.evaluate_all_rules()

        assert result["rules_checked"] == 1
        assert result["alerts_triggered"] == 1
        mock_rule_repo.update.assert_called_once()

    async def test_evaluate_all_rules_threshold_not_met(
        self,
        alert_service,
        mock_rule_repo,
        mock_device_repo,
        mock_bandwidth_repo,
        sample_device,
        sample_bandwidth_rule,
    ):
        """Test rule evaluation when threshold is not met."""
        mock_rule_repo.get_rules_ready_to_trigger.return_value = [sample_bandwidth_rule]
        mock_device_repo.get_all_active.return_value = [sample_device]

        # Mock bandwidth data below threshold
        bandwidth_record = MagicMock()
        bandwidth_record.bytes_received = 1_000_000  # 1 MB
        bandwidth_record.bytes_transmitted = 1_000_000  # 1 MB
        mock_bandwidth_repo.get_by_time_range.return_value = [bandwidth_record]

        result = await alert_service.evaluate_all_rules()

        assert result["rules_checked"] == 1
        assert result["alerts_triggered"] == 0

    async def test_evaluate_rule_device_specific(
        self,
        alert_service,
        mock_device_repo,
        mock_bandwidth_repo,
        sample_device,
        sample_device_rule,
    ):
        """Test evaluation of device-specific rule."""
        mock_device_repo.get.return_value = sample_device
        mock_device_repo.get_all_active.return_value = [sample_device]

        result = await alert_service._evaluate_rule(sample_device_rule)

        # Device exists, so threshold won't be met
        assert result is False
        mock_device_repo.get.assert_called_once_with(sample_device.id)

    async def test_evaluate_rule_device_not_found(
        self, alert_service, mock_device_repo, sample_device_rule
    ):
        """Test evaluation when device is not found."""
        sample_device_rule.device_id = 999
        mock_device_repo.get.return_value = None

        result = await alert_service._evaluate_rule(sample_device_rule)

        assert result is False


@pytest.mark.asyncio
class TestAlertServiceMetrics:
    """Tests for metric value retrieval."""

    async def test_get_bandwidth_usage_metric(
        self, alert_service, mock_bandwidth_repo, sample_device
    ):
        """Test calculating bandwidth usage metric."""
        # Create mock bandwidth records
        record1 = MagicMock()
        record1.bytes_received = 100_000_000  # 100 MB
        record1.bytes_transmitted = 100_000_000  # 100 MB
        record2 = MagicMock()
        record2.bytes_received = 100_000_000
        record2.bytes_transmitted = 100_000_000

        mock_bandwidth_repo.get_by_time_range.return_value = [record1, record2]

        value = await alert_service._get_metric_value(sample_device, AlertMetric.BANDWIDTH_USAGE, 5)

        # Total: 400 MB over 5 minutes (300 seconds)
        # (400 * 1_000_000 * 8) / (300 * 1_000_000) = 10.67 Mbps
        assert value is not None
        assert value > 10.0
        assert value < 11.0

    async def test_get_upload_speed_metric(self, alert_service, mock_bandwidth_repo, sample_device):
        """Test calculating upload speed metric."""
        record = MagicMock()
        record.bytes_transmitted = 150_000_000  # 150 MB
        record.bytes_received = 0

        mock_bandwidth_repo.get_by_time_range.return_value = [record]

        value = await alert_service._get_metric_value(sample_device, AlertMetric.UPLOAD_SPEED, 5)

        # (150 * 1_000_000 * 8) / (300 * 1_000_000) = 4 Mbps
        assert value == 4.0

    async def test_get_download_speed_metric(
        self, alert_service, mock_bandwidth_repo, sample_device
    ):
        """Test calculating download speed metric."""
        record = MagicMock()
        record.bytes_received = 300_000_000  # 300 MB
        record.bytes_transmitted = 0

        mock_bandwidth_repo.get_by_time_range.return_value = [record]

        value = await alert_service._get_metric_value(sample_device, AlertMetric.DOWNLOAD_SPEED, 5)

        # (300 * 1_000_000 * 8) / (300 * 1_000_000) = 8 Mbps
        assert value == 8.0

    async def test_get_total_bytes_metric(self, alert_service, mock_bandwidth_repo, sample_device):
        """Test calculating total bytes metric."""
        record = MagicMock()
        record.bytes_received = 100_000_000  # 100 MB
        record.bytes_transmitted = 50_000_000  # 50 MB

        mock_bandwidth_repo.get_by_time_range.return_value = [record]

        value = await alert_service._get_metric_value(sample_device, AlertMetric.TOTAL_BYTES, 5)

        assert value == 150_000_000.0

    async def test_get_device_count_metric(self, alert_service, mock_device_repo, sample_device):
        """Test calculating device count metric."""
        device1 = MagicMock()
        device2 = MagicMock()
        mock_device_repo.get_all_active.return_value = [device1, device2]

        value = await alert_service._get_metric_value(sample_device, AlertMetric.DEVICE_COUNT, 0)

        assert value == 2.0

    async def test_get_metric_value_no_data(
        self, alert_service, mock_bandwidth_repo, sample_device
    ):
        """Test metric value retrieval when no data available."""
        mock_bandwidth_repo.get_by_time_range.return_value = []

        value = await alert_service._get_metric_value(sample_device, AlertMetric.BANDWIDTH_USAGE, 5)

        assert value is None


@pytest.mark.asyncio
class TestAlertServiceThresholdChecking:
    """Tests for threshold condition checking."""

    def test_check_threshold_greater_than(self, alert_service):
        """Test GREATER_THAN condition."""
        assert alert_service._check_threshold(150.0, AlertCondition.GREATER_THAN, 100.0) is True
        assert alert_service._check_threshold(100.0, AlertCondition.GREATER_THAN, 100.0) is False
        assert alert_service._check_threshold(50.0, AlertCondition.GREATER_THAN, 100.0) is False

    def test_check_threshold_less_than(self, alert_service):
        """Test LESS_THAN condition."""
        assert alert_service._check_threshold(50.0, AlertCondition.LESS_THAN, 100.0) is True
        assert alert_service._check_threshold(100.0, AlertCondition.LESS_THAN, 100.0) is False
        assert alert_service._check_threshold(150.0, AlertCondition.LESS_THAN, 100.0) is False

    def test_check_threshold_equals(self, alert_service):
        """Test EQUALS condition."""
        assert alert_service._check_threshold(100.0, AlertCondition.EQUALS, 100.0) is True
        assert alert_service._check_threshold(100.005, AlertCondition.EQUALS, 100.0) is True
        assert alert_service._check_threshold(100.02, AlertCondition.EQUALS, 100.0) is False

    def test_check_threshold_not_equals(self, alert_service):
        """Test NOT_EQUALS condition."""
        assert alert_service._check_threshold(150.0, AlertCondition.NOT_EQUALS, 100.0) is True
        assert alert_service._check_threshold(100.0, AlertCondition.NOT_EQUALS, 100.0) is False
        assert alert_service._check_threshold(100.005, AlertCondition.NOT_EQUALS, 100.0) is False


@pytest.mark.asyncio
class TestAlertServiceAlertCreation:
    """Tests for alert creation and notification."""

    async def test_create_alert_success(
        self, alert_service, mock_alert_repo, sample_device, sample_bandwidth_rule
    ):
        """Test successful alert creation."""
        created_alert = Alert(
            id=1,
            rule_id=sample_bandwidth_rule.id,
            device_id=sample_device.id,
            title=sample_bandwidth_rule.name,
            message="Test alert",
            severity=sample_bandwidth_rule.severity,
            status=AlertStatus.ACTIVE,
            metric_value=150.0,
            threshold_value=100.0,
            triggered_at=datetime.utcnow(),
            notifications_sent={},
        )
        mock_alert_repo.create.return_value = created_alert

        with patch("asyncio.create_task"):
            alert = await alert_service._create_alert(sample_device, sample_bandwidth_rule, 150.0)

        assert alert.rule_id == sample_bandwidth_rule.id
        assert alert.device_id == sample_device.id
        assert alert.metric_value == 150.0
        mock_alert_repo.create.assert_called_once()

    async def test_generate_alert_message_bandwidth(
        self, alert_service, sample_device, sample_bandwidth_rule
    ):
        """Test alert message generation for bandwidth metrics."""
        message = alert_service._generate_alert_message(sample_device, sample_bandwidth_rule, 150.5)

        assert "test-device" in message
        assert "192.168.1.100" in message
        assert "150.50 Mbps" in message
        assert "100.00 Mbps" in message
        assert "exceeded" in message
        assert "5 minutes" in message

    async def test_generate_alert_message_total_bytes(
        self, alert_service, sample_device, sample_bandwidth_rule
    ):
        """Test alert message generation for total bytes metric."""
        sample_bandwidth_rule.metric = AlertMetric.TOTAL_BYTES
        sample_bandwidth_rule.threshold_value = 500_000_000  # 500 MB

        message = alert_service._generate_alert_message(
            sample_device, sample_bandwidth_rule, 750_000_000
        )

        assert "750.00 MB" in message
        assert "500.00 MB" in message

    async def test_generate_alert_message_device_count(
        self, alert_service, sample_device, sample_device_rule
    ):
        """Test alert message generation for device count metric."""
        message = alert_service._generate_alert_message(sample_device, sample_device_rule, 0)

        assert "test-device" in message
        assert "Device Count" in message
        assert "0" in message

    async def test_send_notifications_success(
        self,
        alert_service,
        mock_notification_manager,
        mock_alert_repo,
        sample_device,
        sample_bandwidth_rule,
    ):
        """Test sending notifications for an alert."""
        alert = Alert(
            id=1,
            rule_id=sample_bandwidth_rule.id,
            device_id=sample_device.id,
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            metric_value=150.0,
            threshold_value=100.0,
            triggered_at=datetime.utcnow(),
            notifications_sent={},
        )

        # Mock notification results
        result = MagicMock()
        result.timestamp = datetime.utcnow()
        result.success = True
        result.error = None
        result.details = {"message_id": "123"}

        mock_notification_manager.send_all_notifications.return_value = {"email": result}

        await alert_service._send_notifications(alert, sample_bandwidth_rule)

        mock_notification_manager.send_all_notifications.assert_called_once_with(
            alert, sample_bandwidth_rule
        )
        mock_alert_repo.update.assert_called_once()


@pytest.mark.asyncio
class TestAlertServiceTestRule:
    """Tests for rule testing functionality."""

    async def test_test_rule_success(
        self,
        alert_service,
        mock_rule_repo,
        mock_device_repo,
        mock_bandwidth_repo,
        sample_device,
        sample_bandwidth_rule,
    ):
        """Test rule testing without triggering alerts."""
        mock_rule_repo.get.return_value = sample_bandwidth_rule
        mock_device_repo.get_all_active.return_value = [sample_device]

        # Mock bandwidth data that exceeds threshold
        record = MagicMock()
        record.bytes_received = 2_000_000_000  # 2 GB
        record.bytes_transmitted = 2_000_000_000  # 2 GB
        mock_bandwidth_repo.get_by_time_range.return_value = [record]

        result = await alert_service.test_rule(sample_bandwidth_rule.id)

        assert result["rule_id"] == sample_bandwidth_rule.id
        assert result["rule_name"] == sample_bandwidth_rule.name
        assert result["devices_checked"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["threshold_met"] is True

    async def test_test_rule_not_found(self, alert_service, mock_rule_repo):
        """Test testing nonexistent rule."""
        mock_rule_repo.get.return_value = None

        with pytest.raises(ValueError, match="Rule .* not found"):
            await alert_service.test_rule(999)

    async def test_test_rule_device_not_found(
        self, alert_service, mock_rule_repo, mock_device_repo, sample_device_rule
    ):
        """Test testing rule when device is not found."""
        sample_device_rule.device_id = 999
        mock_rule_repo.get.return_value = sample_device_rule
        mock_device_repo.get.return_value = None

        result = await alert_service.test_rule(sample_device_rule.id)

        assert "error" in result

    async def test_test_rule_no_data(
        self,
        alert_service,
        mock_rule_repo,
        mock_device_repo,
        mock_bandwidth_repo,
        sample_device,
        sample_bandwidth_rule,
    ):
        """Test rule testing when no metric data available."""
        mock_rule_repo.get.return_value = sample_bandwidth_rule
        mock_device_repo.get_all_active.return_value = [sample_device]
        mock_bandwidth_repo.get_by_time_range.return_value = []

        result = await alert_service.test_rule(sample_bandwidth_rule.id)

        assert result["devices_checked"] == 1
        assert result["results"][0]["metric_value"] is None
        assert result["results"][0]["threshold_met"] is False
        assert "No data available" in result["results"][0]["message"]

    async def test_test_rule_multiple_devices(
        self,
        alert_service,
        mock_rule_repo,
        mock_device_repo,
        mock_bandwidth_repo,
        sample_device,
        sample_bandwidth_rule,
    ):
        """Test rule testing with multiple devices."""
        device2 = Device(
            id=2,
            ip_address="192.168.1.101",
            mac_address="00:11:22:33:44:66",
            hostname="test-device-2",
            device_name="Test Device 2",
            status=DeviceStatus.ACTIVE,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            is_blocked=False,
            is_throttled=False,
            total_bytes_sent=0,
            total_bytes_received=0,
        )

        mock_rule_repo.get.return_value = sample_bandwidth_rule
        mock_device_repo.get_all_active.return_value = [sample_device, device2]

        # Device 1: High bandwidth (exceeds 100 Mbps threshold)
        record1 = MagicMock()
        record1.bytes_received = 2_000_000_000  # 2 GB
        record1.bytes_transmitted = 2_000_000_000  # 2 GB

        # Device 2: Low bandwidth
        record2 = MagicMock()
        record2.bytes_received = 1_000_000
        record2.bytes_transmitted = 1_000_000

        mock_bandwidth_repo.get_by_time_range.side_effect = [[record1], [record2]]

        result = await alert_service.test_rule(sample_bandwidth_rule.id)

        assert result["devices_checked"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["threshold_met"] is True
        assert result["results"][1]["threshold_met"] is False


@pytest.mark.asyncio
class TestAlertServiceEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_evaluate_rules_with_exception(
        self, alert_service, mock_rule_repo, mock_device_repo, sample_bandwidth_rule
    ):
        """Test evaluation continues when individual rule raises exception."""
        mock_rule_repo.get_rules_ready_to_trigger.return_value = [sample_bandwidth_rule]
        mock_device_repo.get_all_active.side_effect = Exception("Database error")

        result = await alert_service.evaluate_all_rules()

        # Should handle exception and continue
        assert result["rules_checked"] == 1
        assert result["alerts_triggered"] == 0

    async def test_check_device_against_rule_no_metric(
        self, alert_service, mock_bandwidth_repo, sample_device, sample_bandwidth_rule
    ):
        """Test checking device when metric value is None."""
        mock_bandwidth_repo.get_by_time_range.return_value = []

        result = await alert_service._check_device_against_rule(
            sample_device, sample_bandwidth_rule
        )

        assert result is False

    async def test_alert_service_initialization_default_dependencies(self, db_session):
        """Test service initializes with default dependencies."""
        service = AlertService(session=db_session)

        assert service.alert_repo is not None
        assert service.rule_repo is not None
        assert service.device_repo is not None
        assert service.bandwidth_repo is not None
        assert service.notification_manager is not None
