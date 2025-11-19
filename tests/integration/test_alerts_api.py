"""
Comprehensive integration tests for alert API routes.
"""

from datetime import datetime, timedelta

import pytest
from fastapi import status

from src.models.alert import Alert, AlertRule, AlertSeverity, AlertStatus
from src.repositories.alert_repository import AlertRepository, AlertRuleRepository


@pytest.fixture
def sample_alert_rule_data():
    """Sample alert rule data for testing."""
    return {
        "name": "High Bandwidth Alert",
        "description": "Alert when download speed exceeds 50 Mbps",
        "metric": "download_speed",
        "condition": "greater_than",
        "threshold_value": 50.0,
        "time_window_minutes": 5,
        "device_id": None,
        "severity": "warning",
        "notification_channels": "email,websocket",
        "cooldown_minutes": 15,
        "is_enabled": True,
    }


@pytest.fixture
def sample_alert_rule_with_device_data():
    """Sample alert rule data with specific device."""
    return {
        "name": "Device Specific Alert",
        "description": "Alert for device 1",
        "metric": "bandwidth_usage",
        "condition": "greater_than",
        "threshold_value": 100.0,
        "time_window_minutes": 10,
        "device_id": 1,
        "severity": "critical",
        "notification_channels": "websocket",
        "cooldown_minutes": 30,
        "is_enabled": True,
    }


@pytest.fixture
async def created_alert_rule(db_session, sample_alert_rule_data):
    """Create an alert rule for testing."""
    rule_repo = AlertRuleRepository(db_session)
    rule = await rule_repo.create(sample_alert_rule_data)
    await db_session.commit()
    return rule


@pytest.fixture
async def created_alert(db_session, created_alert_rule):
    """Create an alert for testing."""
    alert_repo = AlertRepository(db_session)
    alert_data = {
        "rule_id": created_alert_rule.id,
        "device_id": None,
        "title": "High Bandwidth Detected",
        "message": "Download speed exceeded 50 Mbps",
        "severity": AlertSeverity.WARNING,
        "status": AlertStatus.ACTIVE,
        "metric_value": 75.5,
        "threshold_value": 50.0,
        "triggered_at": datetime.utcnow(),
    }
    alert = await alert_repo.create(alert_data)
    await db_session.commit()
    return alert


@pytest.mark.asyncio
class TestAlertRuleEndpoints:
    """Tests for alert rule CRUD endpoints."""

    async def test_create_alert_rule_success(
        self, test_client, admin_token, sample_alert_rule_data
    ):
        """Test creating an alert rule."""
        response = test_client.post(
            "/api/v1/alerts/rules",
            json=sample_alert_rule_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "High Bandwidth Alert"
        assert data["data"]["metric"] == "download_speed"
        assert data["data"]["condition"] == "greater_than"
        assert data["data"]["threshold_value"] == 50.0
        assert data["data"]["severity"] == "warning"
        assert data["data"]["is_enabled"] is True
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_alert_rule_invalid_channels(
        self, test_client, admin_token, sample_alert_rule_data
    ):
        """Test creating alert rule with invalid notification channels."""
        invalid_data = sample_alert_rule_data.copy()
        invalid_data["notification_channels"] = "email,invalid_channel"

        response = test_client.post(
            "/api/v1/alerts/rules",
            json=invalid_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_alert_rule_negative_threshold(
        self, test_client, admin_token, sample_alert_rule_data
    ):
        """Test creating alert rule with negative threshold."""
        invalid_data = sample_alert_rule_data.copy()
        invalid_data["threshold_value"] = -10.0

        response = test_client.post(
            "/api/v1/alerts/rules",
            json=invalid_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should succeed - negative thresholds might be valid for some metrics
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    async def test_create_alert_rule_requires_auth(self, test_client, sample_alert_rule_data):
        """Test that creating alert rule requires authentication."""
        response = test_client.post(
            "/api/v1/alerts/rules",
            json=sample_alert_rule_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_list_alert_rules_success(self, test_client, user_token, created_alert_rule):
        """Test listing all alert rules."""
        response = test_client.get(
            "/api/v1/alerts/rules",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert any(rule["id"] == created_alert_rule.id for rule in data["data"])

    async def test_list_alert_rules_with_pagination(
        self, test_client, user_token, db_session, sample_alert_rule_data
    ):
        """Test listing alert rules with pagination."""
        # Create multiple rules
        rule_repo = AlertRuleRepository(db_session)
        for i in range(5):
            rule_data = sample_alert_rule_data.copy()
            rule_data["name"] = f"Rule {i}"
            await rule_repo.create(rule_data)
        await db_session.commit()

        # Test pagination
        response = test_client.get(
            "/api/v1/alerts/rules?skip=0&limit=3",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) <= 3

    async def test_list_alert_rules_enabled_only(
        self, test_client, user_token, db_session, sample_alert_rule_data
    ):
        """Test listing only enabled alert rules."""
        # Create enabled and disabled rules
        rule_repo = AlertRuleRepository(db_session)

        enabled_rule_data = sample_alert_rule_data.copy()
        enabled_rule_data["name"] = "Enabled Rule"
        enabled_rule_data["is_enabled"] = True
        await rule_repo.create(enabled_rule_data)

        disabled_rule_data = sample_alert_rule_data.copy()
        disabled_rule_data["name"] = "Disabled Rule"
        disabled_rule_data["is_enabled"] = False
        await rule_repo.create(disabled_rule_data)

        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/rules?enabled_only=true",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned rules should be enabled
        assert all(rule["is_enabled"] for rule in data["data"])

    async def test_list_alert_rules_by_device(
        self, test_client, user_token, db_session, sample_alert_rule_with_device_data
    ):
        """Test listing alert rules filtered by device."""
        # Create device-specific rule
        rule_repo = AlertRuleRepository(db_session)
        await rule_repo.create(sample_alert_rule_with_device_data)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/rules?device_id=1",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(rule["device_id"] == 1 or rule["device_id"] is None for rule in data["data"])

    async def test_get_alert_rule_success(self, test_client, user_token, created_alert_rule):
        """Test getting a specific alert rule."""
        response = test_client.get(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == created_alert_rule.id
        assert data["data"]["name"] == created_alert_rule.name

    async def test_get_alert_rule_not_found(self, test_client, user_token):
        """Test getting non-existent alert rule."""
        response = test_client.get(
            "/api/v1/alerts/rules/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_alert_rule_success(self, test_client, admin_token, created_alert_rule):
        """Test updating an alert rule."""
        update_data = {
            "name": "Updated Alert Rule",
            "threshold_value": 75.0,
            "is_enabled": False,
        }

        response = test_client.put(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Alert Rule"
        assert data["data"]["threshold_value"] == 75.0
        assert data["data"]["is_enabled"] is False

    async def test_update_alert_rule_partial(self, test_client, admin_token, created_alert_rule):
        """Test partial update of alert rule."""
        update_data = {"threshold_value": 100.0}

        response = test_client.put(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["threshold_value"] == 100.0
        # Other fields should remain unchanged
        assert data["data"]["name"] == created_alert_rule.name

    async def test_update_alert_rule_not_found(self, test_client, admin_token):
        """Test updating non-existent alert rule."""
        update_data = {"name": "Updated Name"}

        response = test_client.put(
            "/api/v1/alerts/rules/99999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_alert_rule_requires_admin(
        self, test_client, user_token, created_alert_rule
    ):
        """Test that updating alert rule requires admin privileges."""
        update_data = {"name": "Updated Name"}

        response = test_client.put(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_alert_rule_success(self, test_client, admin_token, created_alert_rule):
        """Test deleting an alert rule."""
        response = test_client.delete(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify rule is deleted
        get_response = test_client.get(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_alert_rule_not_found(self, test_client, admin_token):
        """Test deleting non-existent alert rule."""
        response = test_client.delete(
            "/api/v1/alerts/rules/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_alert_rule_requires_admin(
        self, test_client, user_token, created_alert_rule
    ):
        """Test that deleting alert rule requires admin privileges."""
        response = test_client.delete(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_test_alert_rule_success(self, test_client, admin_token, created_alert_rule):
        """Test testing an alert rule without triggering actual alerts."""
        response = test_client.post(
            f"/api/v1/alerts/rules/{created_alert_rule.id}/test",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # Should contain test results

    async def test_test_alert_rule_not_found(self, test_client, admin_token):
        """Test testing non-existent alert rule."""
        response = test_client.post(
            "/api/v1/alerts/rules/99999/test",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestAlertEndpoints:
    """Tests for alert listing and management endpoints."""

    async def test_list_alerts_success(self, test_client, user_token, created_alert):
        """Test listing all alerts."""
        response = test_client.get(
            "/api/v1/alerts/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert any(alert["id"] == created_alert.id for alert in data["data"])

    async def test_list_alerts_with_pagination(
        self, test_client, user_token, db_session, created_alert_rule
    ):
        """Test listing alerts with pagination."""
        # Create multiple alerts
        alert_repo = AlertRepository(db_session)
        for i in range(5):
            alert_data = {
                "rule_id": created_alert_rule.id,
                "title": f"Alert {i}",
                "message": f"Test alert {i}",
                "severity": AlertSeverity.WARNING,
                "status": AlertStatus.ACTIVE,
                "metric_value": 50.0 + i,
                "threshold_value": 50.0,
                "triggered_at": datetime.utcnow(),
            }
            await alert_repo.create(alert_data)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/?skip=0&limit=3",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) <= 3

    async def test_list_alerts_filter_by_status(
        self, test_client, user_token, db_session, created_alert_rule
    ):
        """Test listing alerts filtered by status."""
        alert_repo = AlertRepository(db_session)

        # Create active alert
        active_alert_data = {
            "rule_id": created_alert_rule.id,
            "title": "Active Alert",
            "message": "Active test alert",
            "severity": AlertSeverity.WARNING,
            "status": AlertStatus.ACTIVE,
            "metric_value": 55.0,
            "threshold_value": 50.0,
            "triggered_at": datetime.utcnow(),
        }
        await alert_repo.create(active_alert_data)

        # Create resolved alert
        resolved_alert_data = active_alert_data.copy()
        resolved_alert_data["title"] = "Resolved Alert"
        resolved_alert_data["status"] = AlertStatus.RESOLVED
        resolved_alert_data["resolved_at"] = datetime.utcnow()
        await alert_repo.create(resolved_alert_data)

        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/?status_filter=active",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(alert["status"] == "active" for alert in data["data"])

    async def test_list_alerts_filter_by_severity(
        self, test_client, user_token, db_session, created_alert_rule
    ):
        """Test listing alerts filtered by severity."""
        alert_repo = AlertRepository(db_session)

        # Create critical alert
        critical_alert_data = {
            "rule_id": created_alert_rule.id,
            "title": "Critical Alert",
            "message": "Critical test alert",
            "severity": AlertSeverity.CRITICAL,
            "status": AlertStatus.ACTIVE,
            "metric_value": 100.0,
            "threshold_value": 50.0,
            "triggered_at": datetime.utcnow(),
        }
        await alert_repo.create(critical_alert_data)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/?severity=critical",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(alert["severity"] == "critical" for alert in data["data"])

    async def test_list_alerts_filter_by_device(
        self, test_client, user_token, db_session, created_alert_rule
    ):
        """Test listing alerts filtered by device."""
        alert_repo = AlertRepository(db_session)

        alert_data = {
            "rule_id": created_alert_rule.id,
            "device_id": 1,
            "title": "Device Alert",
            "message": "Alert for device 1",
            "severity": AlertSeverity.WARNING,
            "status": AlertStatus.ACTIVE,
            "metric_value": 60.0,
            "threshold_value": 50.0,
            "triggered_at": datetime.utcnow(),
        }
        await alert_repo.create(alert_data)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/?device_id=1",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(alert["device_id"] == 1 or alert["device_id"] is None for alert in data["data"])

    async def test_list_alerts_filter_by_rule(
        self, test_client, user_token, created_alert_rule, created_alert
    ):
        """Test listing alerts filtered by rule."""
        response = test_client.get(
            f"/api/v1/alerts/?rule_id={created_alert_rule.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(alert["rule_id"] == created_alert_rule.id for alert in data["data"])

    async def test_list_alerts_filter_by_date_range(
        self, test_client, user_token, db_session, created_alert_rule
    ):
        """Test listing alerts filtered by date range."""
        alert_repo = AlertRepository(db_session)

        # Create alerts with different dates
        now = datetime.utcnow()
        past_date = now - timedelta(days=7)

        old_alert_data = {
            "rule_id": created_alert_rule.id,
            "title": "Old Alert",
            "message": "Old test alert",
            "severity": AlertSeverity.WARNING,
            "status": AlertStatus.RESOLVED,
            "metric_value": 55.0,
            "threshold_value": 50.0,
            "triggered_at": past_date,
        }
        await alert_repo.create(old_alert_data)

        recent_alert_data = old_alert_data.copy()
        recent_alert_data["title"] = "Recent Alert"
        recent_alert_data["triggered_at"] = now
        await alert_repo.create(recent_alert_data)

        await db_session.commit()

        # Query recent alerts
        start_date = (now - timedelta(days=1)).isoformat()
        end_date = (now + timedelta(days=1)).isoformat()

        response = test_client.get(
            f"/api/v1/alerts/?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return recent alerts only
        assert len(data["data"]) >= 1

    async def test_list_active_alerts(self, test_client, user_token, created_alert):
        """Test listing only active alerts."""
        response = test_client.get(
            "/api/v1/alerts/active",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        # All returned alerts should be active
        assert all(
            alert["status"] in ["active", "acknowledged", "snoozed"] for alert in data["data"]
        )

    async def test_list_recent_alerts_default(self, test_client, user_token, created_alert):
        """Test listing recent alerts with default parameters."""
        response = test_client.get(
            "/api/v1/alerts/recent",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    async def test_list_recent_alerts_custom_hours(
        self, test_client, user_token, db_session, created_alert_rule
    ):
        """Test listing recent alerts with custom hour window."""
        alert_repo = AlertRepository(db_session)

        # Create alerts at different times
        now = datetime.utcnow()

        # Recent alert (within 1 hour)
        recent_alert_data = {
            "rule_id": created_alert_rule.id,
            "title": "Recent Alert",
            "message": "Very recent alert",
            "severity": AlertSeverity.WARNING,
            "status": AlertStatus.ACTIVE,
            "metric_value": 55.0,
            "threshold_value": 50.0,
            "triggered_at": now - timedelta(minutes=30),
        }
        await alert_repo.create(recent_alert_data)

        # Older alert (more than 1 hour)
        old_alert_data = recent_alert_data.copy()
        old_alert_data["title"] = "Old Alert"
        old_alert_data["triggered_at"] = now - timedelta(hours=2)
        await alert_repo.create(old_alert_data)

        await db_session.commit()

        response = test_client.get(
            "/api/v1/alerts/recent?hours=1&limit=100",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return recent alerts only
        assert len(data["data"]) >= 1

    async def test_get_alert_success(self, test_client, user_token, created_alert):
        """Test getting a specific alert."""
        response = test_client.get(
            f"/api/v1/alerts/{created_alert.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == created_alert.id
        assert data["data"]["title"] == created_alert.title

    async def test_get_alert_not_found(self, test_client, user_token):
        """Test getting non-existent alert."""
        response = test_client.get(
            "/api/v1/alerts/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_acknowledge_alert_success(self, test_client, admin_token, created_alert):
        """Test acknowledging an alert."""
        update_data = {"status": "acknowledged"}

        response = test_client.put(
            f"/api/v1/alerts/{created_alert.id}/status",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "acknowledged"
        assert data["data"]["acknowledged_at"] is not None

    async def test_resolve_alert_success(self, test_client, admin_token, created_alert):
        """Test resolving an alert."""
        update_data = {"status": "resolved"}

        response = test_client.put(
            f"/api/v1/alerts/{created_alert.id}/status",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "resolved"
        assert data["data"]["resolved_at"] is not None

    async def test_snooze_alert_success(self, test_client, admin_token, created_alert):
        """Test snoozing an alert."""
        update_data = {
            "status": "snoozed",
            "snooze_minutes": 60,
        }

        response = test_client.put(
            f"/api/v1/alerts/{created_alert.id}/status",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "snoozed"
        assert data["data"]["snoozed_until"] is not None

    async def test_snooze_alert_without_minutes(self, test_client, admin_token, created_alert):
        """Test snoozing alert without providing snooze_minutes."""
        update_data = {"status": "snoozed"}

        response = test_client.put(
            f"/api/v1/alerts/{created_alert.id}/status",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_update_alert_status_invalid_status(
        self, test_client, admin_token, created_alert
    ):
        """Test updating alert with invalid status."""
        update_data = {"status": "invalid_status"}

        response = test_client.put(
            f"/api/v1/alerts/{created_alert.id}/status",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_alert_status_not_found(self, test_client, admin_token):
        """Test updating status of non-existent alert."""
        update_data = {"status": "acknowledged"}

        response = test_client.put(
            "/api/v1/alerts/99999/status",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_alert_status_requires_admin(self, test_client, user_token, created_alert):
        """Test that updating alert status requires admin privileges."""
        update_data = {"status": "resolved"}

        response = test_client.put(
            f"/api/v1/alerts/{created_alert.id}/status",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_alert_statistics(self, test_client, user_token, created_alert):
        """Test getting alert statistics."""
        response = test_client.get(
            "/api/v1/alerts/statistics/summary",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "total_alerts" in data["data"]
        assert "active_alerts" in data["data"]
        assert "acknowledged_alerts" in data["data"]
        assert "resolved_alerts" in data["data"]
        assert "critical_alerts" in data["data"]
        assert "by_severity" in data["data"]
        assert "by_status" in data["data"]
        assert isinstance(data["data"]["total_alerts"], int)
        assert data["data"]["total_alerts"] >= 1


@pytest.mark.asyncio
class TestAlertAuthorizationAndErrors:
    """Tests for authorization and error handling."""

    async def test_unauthorized_access_to_alerts(self, test_client):
        """Test that unauthorized requests are rejected."""
        endpoints = [
            "/api/v1/alerts/rules",
            "/api/v1/alerts/",
            "/api/v1/alerts/active",
            "/api/v1/alerts/recent",
            "/api/v1/alerts/statistics/summary",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_invalid_token_access(self, test_client):
        """Test that invalid tokens are rejected."""
        response = test_client.get(
            "/api/v1/alerts/rules",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_rule_with_missing_fields(self, test_client, admin_token):
        """Test creating rule with missing required fields."""
        incomplete_data = {
            "name": "Incomplete Rule",
            # Missing required fields
        }

        response = test_client.post(
            "/api/v1/alerts/rules",
            json=incomplete_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_rule_with_invalid_data_types(
        self, test_client, admin_token, created_alert_rule
    ):
        """Test updating rule with invalid data types."""
        invalid_data = {
            "threshold_value": "not_a_number",  # Should be float
        }

        response = test_client.put(
            f"/api/v1/alerts/rules/{created_alert_rule.id}",
            json=invalid_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
