"""
Unit tests for advanced controls API routes.
"""

from datetime import time

import pytest
from fastapi import status

from src.models.advanced_controls import BandwidthQuota, QoSPolicy, ThrottleSchedule
from src.repositories.advanced_controls_repository import (
    BandwidthQuotaRepository,
    QoSPolicyRepository,
    ThrottleScheduleRepository,
)


@pytest.fixture
def sample_quota_data():
    """Sample bandwidth quota data for testing."""
    return {
        "device_id": 1,
        "quota_name": "Monthly Limit",
        "limit_bytes": 100_000_000_000,  # 100 GB
        "period": "monthly",
        "reset_day": 1,
    }


@pytest.fixture
def sample_qos_policy_data():
    """Sample QoS policy data for testing."""
    return {
        "policy_name": "High Priority Video",
        "description": "Prioritize video streaming traffic",
        "priority": "high",
        "protocol": "tcp",
        "port_range": "1935,8080-8090",
        "bandwidth_limit_mbps": 50,
    }


@pytest.fixture
def sample_schedule_data():
    """Sample throttle schedule data for testing."""
    return {
        "device_id": 1,
        "schedule_name": "Night Throttle",
        "start_time": "22:00:00",
        "end_time": "06:00:00",
        "days_of_week": "0,1,2,3,4,5,6",  # All days
        "throttle_limit_mbps": 10,
    }


@pytest.mark.asyncio
class TestBandwidthQuotaEndpoints:
    """Tests for bandwidth quota endpoints."""

    async def test_create_quota_success(
        self, test_client, admin_token, db_session, sample_quota_data
    ):
        """Test creating a bandwidth quota."""
        response = test_client.post(
            "/api/v1/advanced-controls/quotas",
            json=sample_quota_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["quota_name"] == "Monthly Limit"
        assert data["data"]["limit_bytes"] == 100_000_000_000
        assert data["data"]["used_bytes"] == 0
        assert data["data"]["is_active"] is True

    async def test_create_quota_requires_admin(self, test_client, user_token, sample_quota_data):
        """Test that creating quota requires admin privileges."""
        response = test_client.post(
            "/api/v1/advanced-controls/quotas",
            json=sample_quota_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_quota_no_auth(self, test_client, sample_quota_data):
        """Test that creating quota requires authentication."""
        response = test_client.post(
            "/api/v1/advanced-controls/quotas",
            json=sample_quota_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_list_quotas_success(self, test_client, user_token, db_session):
        """Test listing bandwidth quotas."""
        # Create test quotas
        repo = BandwidthQuotaRepository(db_session)
        for i in range(3):
            quota = BandwidthQuota(
                device_id=i + 1,
                quota_name=f"Quota {i}",
                limit_bytes=100_000_000_000,
                used_bytes=0,
                period="monthly",
                reset_day=1,
                is_active=True,
            )
            await repo.create(quota.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/quotas",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3

    async def test_list_quotas_filter_by_device(self, test_client, user_token, db_session):
        """Test listing quotas filtered by device ID."""
        repo = BandwidthQuotaRepository(db_session)
        for i in range(3):
            quota = BandwidthQuota(
                device_id=1 if i < 2 else 2,
                quota_name=f"Quota {i}",
                limit_bytes=100_000_000_000,
                used_bytes=0,
                period="monthly",
                reset_day=1,
                is_active=True,
            )
            await repo.create(quota.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/quotas?device_id=1",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2

    async def test_list_quotas_active_only(self, test_client, user_token, db_session):
        """Test listing only active quotas."""
        repo = BandwidthQuotaRepository(db_session)
        for i in range(3):
            quota = BandwidthQuota(
                device_id=i + 1,
                quota_name=f"Quota {i}",
                limit_bytes=100_000_000_000,
                used_bytes=0,
                period="monthly",
                reset_day=1,
                is_active=(i < 2),  # First 2 are active
            )
            await repo.create(quota.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/quotas?active_only=true",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2

    async def test_update_quota_success(
        self, test_client, admin_token, db_session, sample_quota_data
    ):
        """Test updating a bandwidth quota."""
        # Create quota first
        repo = BandwidthQuotaRepository(db_session)
        quota = await repo.create({**sample_quota_data, "used_bytes": 0, "is_active": True})
        await db_session.commit()

        update_data = {"quota_name": "Updated Limit", "limit_bytes": 200_000_000_000}
        response = test_client.put(
            f"/api/v1/advanced-controls/quotas/{quota.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["quota_name"] == "Updated Limit"
        assert data["data"]["limit_bytes"] == 200_000_000_000

    async def test_update_quota_not_found(self, test_client, admin_token):
        """Test updating nonexistent quota."""
        response = test_client.put(
            "/api/v1/advanced-controls/quotas/9999",
            json={"quota_name": "Updated"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_reset_quota_success(
        self, test_client, admin_token, db_session, sample_quota_data
    ):
        """Test resetting a quota's used bytes."""
        # Create quota with used bytes
        repo = BandwidthQuotaRepository(db_session)
        quota = await repo.create(
            {**sample_quota_data, "used_bytes": 50_000_000_000, "is_active": True}
        )
        await db_session.commit()

        response = test_client.post(
            f"/api/v1/advanced-controls/quotas/{quota.id}/reset",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["used_bytes"] == 0

    async def test_reset_quota_not_found(self, test_client, admin_token):
        """Test resetting nonexistent quota."""
        response = test_client.post(
            "/api/v1/advanced-controls/quotas/9999/reset",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_quota_success(
        self, test_client, admin_token, db_session, sample_quota_data
    ):
        """Test deleting a bandwidth quota."""
        repo = BandwidthQuotaRepository(db_session)
        quota = await repo.create({**sample_quota_data, "used_bytes": 0, "is_active": True})
        await db_session.commit()

        response = test_client.delete(
            f"/api/v1/advanced-controls/quotas/{quota.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        deleted_quota = await repo.get(quota.id)
        assert deleted_quota is None

    async def test_delete_quota_not_found(self, test_client, admin_token):
        """Test deleting nonexistent quota."""
        response = test_client.delete(
            "/api/v1/advanced-controls/quotas/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestQoSPolicyEndpoints:
    """Tests for QoS policy endpoints."""

    async def test_create_qos_policy_success(
        self, test_client, admin_token, db_session, sample_qos_policy_data
    ):
        """Test creating a QoS policy."""
        response = test_client.post(
            "/api/v1/advanced-controls/qos-policies",
            json=sample_qos_policy_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["policy_name"] == "High Priority Video"
        assert data["data"]["priority"] == "high"
        assert data["data"]["is_enabled"] is True

    async def test_create_qos_policy_duplicate_name(
        self, test_client, admin_token, db_session, sample_qos_policy_data
    ):
        """Test creating QoS policy with duplicate name."""
        # Create first policy
        repo = QoSPolicyRepository(db_session)
        await repo.create({**sample_qos_policy_data, "is_enabled": True})
        await db_session.commit()

        # Try to create duplicate
        response = test_client.post(
            "/api/v1/advanced-controls/qos-policies",
            json=sample_qos_policy_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_qos_policy_requires_admin(
        self, test_client, user_token, sample_qos_policy_data
    ):
        """Test that creating QoS policy requires admin."""
        response = test_client.post(
            "/api/v1/advanced-controls/qos-policies",
            json=sample_qos_policy_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_list_qos_policies_success(self, test_client, user_token, db_session):
        """Test listing QoS policies."""
        repo = QoSPolicyRepository(db_session)
        for i in range(3):
            policy = QoSPolicy(
                policy_name=f"Policy {i}",
                description="Test policy",
                priority="medium",
                protocol="tcp",
                bandwidth_limit_mbps=50,
                is_enabled=True,
            )
            await repo.create(policy.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/qos-policies",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 3

    async def test_list_qos_policies_filter_by_priority(
        self, test_client, user_token, db_session
    ):
        """Test listing policies filtered by priority."""
        repo = QoSPolicyRepository(db_session)
        priorities = ["high", "medium", "low"]
        for i, priority in enumerate(priorities):
            policy = QoSPolicy(
                policy_name=f"Policy {i}",
                description="Test policy",
                priority=priority,
                protocol="tcp",
                bandwidth_limit_mbps=50,
                is_enabled=True,
            )
            await repo.create(policy.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/qos-policies?priority=high",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["priority"] == "high"

    async def test_list_qos_policies_enabled_only(self, test_client, user_token, db_session):
        """Test listing only enabled policies."""
        repo = QoSPolicyRepository(db_session)
        for i in range(3):
            policy = QoSPolicy(
                policy_name=f"Policy {i}",
                description="Test policy",
                priority="medium",
                protocol="tcp",
                bandwidth_limit_mbps=50,
                is_enabled=(i < 2),  # First 2 are enabled
            )
            await repo.create(policy.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/qos-policies?enabled_only=true",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2

    async def test_update_qos_policy_success(
        self, test_client, admin_token, db_session, sample_qos_policy_data
    ):
        """Test updating a QoS policy."""
        repo = QoSPolicyRepository(db_session)
        policy = await repo.create({**sample_qos_policy_data, "is_enabled": True})
        await db_session.commit()

        update_data = {"priority": "critical", "bandwidth_limit_mbps": 100}
        response = test_client.put(
            f"/api/v1/advanced-controls/qos-policies/{policy.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["priority"] == "critical"
        assert data["data"]["bandwidth_limit_mbps"] == 100

    async def test_update_qos_policy_not_found(self, test_client, admin_token):
        """Test updating nonexistent policy."""
        response = test_client.put(
            "/api/v1/advanced-controls/qos-policies/9999",
            json={"priority": "high"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_qos_policy_success(
        self, test_client, admin_token, db_session, sample_qos_policy_data
    ):
        """Test deleting a QoS policy."""
        repo = QoSPolicyRepository(db_session)
        policy = await repo.create({**sample_qos_policy_data, "is_enabled": True})
        await db_session.commit()

        response = test_client.delete(
            f"/api/v1/advanced-controls/qos-policies/{policy.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_qos_policy_not_found(self, test_client, admin_token):
        """Test deleting nonexistent policy."""
        response = test_client.delete(
            "/api/v1/advanced-controls/qos-policies/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestThrottleScheduleEndpoints:
    """Tests for throttle schedule endpoints."""

    async def test_create_schedule_success(
        self, test_client, admin_token, db_session, sample_schedule_data
    ):
        """Test creating a throttle schedule."""
        response = test_client.post(
            "/api/v1/advanced-controls/schedules",
            json=sample_schedule_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["schedule_name"] == "Night Throttle"
        assert data["data"]["throttle_limit_mbps"] == 10
        assert data["data"]["is_enabled"] is True

    async def test_create_schedule_requires_admin(self, test_client, user_token, sample_schedule_data):
        """Test that creating schedule requires admin."""
        response = test_client.post(
            "/api/v1/advanced-controls/schedules",
            json=sample_schedule_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_list_schedules_success(self, test_client, user_token, db_session):
        """Test listing throttle schedules."""
        repo = ThrottleScheduleRepository(db_session)
        for i in range(3):
            schedule = ThrottleSchedule(
                device_id=i + 1,
                schedule_name=f"Schedule {i}",
                start_time=time(22, 0),
                end_time=time(6, 0),
                days_of_week="0,1,2,3,4,5,6",
                throttle_limit_mbps=10,
                is_enabled=True,
            )
            await repo.create(schedule.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/schedules",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 3

    async def test_list_schedules_filter_by_device(self, test_client, user_token, db_session):
        """Test listing schedules filtered by device ID."""
        repo = ThrottleScheduleRepository(db_session)
        for i in range(3):
            schedule = ThrottleSchedule(
                device_id=1 if i < 2 else 2,
                schedule_name=f"Schedule {i}",
                start_time=time(22, 0),
                end_time=time(6, 0),
                days_of_week="0,1,2,3,4,5,6",
                throttle_limit_mbps=10,
                is_enabled=True,
            )
            await repo.create(schedule.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/schedules?device_id=1",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2

    async def test_list_schedules_enabled_only(self, test_client, user_token, db_session):
        """Test listing only enabled schedules."""
        repo = ThrottleScheduleRepository(db_session)
        for i in range(3):
            schedule = ThrottleSchedule(
                device_id=i + 1,
                schedule_name=f"Schedule {i}",
                start_time=time(22, 0),
                end_time=time(6, 0),
                days_of_week="0,1,2,3,4,5,6",
                throttle_limit_mbps=10,
                is_enabled=(i < 2),  # First 2 are enabled
            )
            await repo.create(schedule.__dict__)
        await db_session.commit()

        response = test_client.get(
            "/api/v1/advanced-controls/schedules?enabled_only=true",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2

    async def test_update_schedule_success(
        self, test_client, admin_token, db_session, sample_schedule_data
    ):
        """Test updating a throttle schedule."""
        repo = ThrottleScheduleRepository(db_session)
        schedule = await repo.create({**sample_schedule_data, "is_enabled": True})
        await db_session.commit()

        update_data = {"throttle_limit_mbps": 20, "is_enabled": False}
        response = test_client.put(
            f"/api/v1/advanced-controls/schedules/{schedule.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["throttle_limit_mbps"] == 20
        assert data["data"]["is_enabled"] is False

    async def test_update_schedule_not_found(self, test_client, admin_token):
        """Test updating nonexistent schedule."""
        response = test_client.put(
            "/api/v1/advanced-controls/schedules/9999",
            json={"throttle_limit_mbps": 20},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_schedule_success(
        self, test_client, admin_token, db_session, sample_schedule_data
    ):
        """Test deleting a throttle schedule."""
        repo = ThrottleScheduleRepository(db_session)
        schedule = await repo.create({**sample_schedule_data, "is_enabled": True})
        await db_session.commit()

        response = test_client.delete(
            f"/api/v1/advanced-controls/schedules/{schedule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_schedule_not_found(self, test_client, admin_token):
        """Test deleting nonexistent schedule."""
        response = test_client.delete(
            "/api/v1/advanced-controls/schedules/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestAdvancedControlsAuth:
    """Tests for authentication and authorization."""

    async def test_endpoints_require_authentication(self, test_client):
        """Test that all endpoints require authentication."""
        endpoints = [
            ("POST", "/api/v1/advanced-controls/quotas", {"quota_name": "Test"}),
            ("GET", "/api/v1/advanced-controls/quotas", None),
            ("PUT", "/api/v1/advanced-controls/quotas/1", {"quota_name": "Test"}),
            ("DELETE", "/api/v1/advanced-controls/quotas/1", None),
            ("POST", "/api/v1/advanced-controls/qos-policies", {"policy_name": "Test"}),
            ("GET", "/api/v1/advanced-controls/qos-policies", None),
            ("PUT", "/api/v1/advanced-controls/qos-policies/1", {"priority": "high"}),
            ("DELETE", "/api/v1/advanced-controls/qos-policies/1", None),
            ("POST", "/api/v1/advanced-controls/schedules", {"schedule_name": "Test"}),
            ("GET", "/api/v1/advanced-controls/schedules", None),
            ("PUT", "/api/v1/advanced-controls/schedules/1", {"is_enabled": False}),
            ("DELETE", "/api/v1/advanced-controls/schedules/1", None),
        ]

        for method, endpoint, json_data in endpoints:
            if method == "GET":
                response = test_client.get(endpoint)
            elif method == "POST":
                response = test_client.post(endpoint, json=json_data)
            elif method == "PUT":
                response = test_client.put(endpoint, json=json_data)
            elif method == "DELETE":
                response = test_client.delete(endpoint)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_write_endpoints_require_admin(
        self, test_client, user_token, sample_quota_data, sample_qos_policy_data, sample_schedule_data
    ):
        """Test that write operations require admin privileges."""
        write_operations = [
            ("POST", "/api/v1/advanced-controls/quotas", sample_quota_data),
            ("PUT", "/api/v1/advanced-controls/quotas/1", {"quota_name": "Test"}),
            ("DELETE", "/api/v1/advanced-controls/quotas/1", None),
            ("POST", "/api/v1/advanced-controls/qos-policies", sample_qos_policy_data),
            ("PUT", "/api/v1/advanced-controls/qos-policies/1", {"priority": "high"}),
            ("DELETE", "/api/v1/advanced-controls/qos-policies/1", None),
            ("POST", "/api/v1/advanced-controls/schedules", sample_schedule_data),
            ("PUT", "/api/v1/advanced-controls/schedules/1", {"is_enabled": False}),
            ("DELETE", "/api/v1/advanced-controls/schedules/1", None),
        ]

        for method, endpoint, json_data in write_operations:
            headers = {"Authorization": f"Bearer {user_token}"}
            if method == "POST":
                response = test_client.post(endpoint, json=json_data, headers=headers)
            elif method == "PUT":
                response = test_client.put(endpoint, json=json_data, headers=headers)
            elif method == "DELETE":
                response = test_client.delete(endpoint, headers=headers)

            assert response.status_code == status.HTTP_403_FORBIDDEN
