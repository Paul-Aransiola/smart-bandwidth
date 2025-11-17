"""
Alert management API routes.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.alert import AlertSeverity, AlertStatus
from src.repositories.alert_repository import AlertRepository, AlertRuleRepository
from src.schemas.alert import (
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertStatistics,
    AlertUpdateStatus,
)
from src.schemas.response import APIResponse
from src.services.alert_service import AlertService
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# Alert Rule Endpoints


@router.post(
    "/rules",
    response_model=APIResponse[AlertRuleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_alert_rule(
    rule_data: AlertRuleCreate, db: AsyncSession = Depends(get_db)
) -> APIResponse[AlertRuleResponse]:
    """Create a new alert rule."""
    try:
        rule_repo = AlertRuleRepository(db)
        rule = await rule_repo.create(rule_data.model_dump())

        return APIResponse(
            success=True,
            message="Alert rule created successfully",
            data=AlertRuleResponse.model_validate(rule),
        )

    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert rule: {str(e)}",
        ) from e


@router.get("/rules", response_model=APIResponse[list[AlertRuleResponse]])
async def list_alert_rules(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    device_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[AlertRuleResponse]]:
    """
    List alert rules.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        enabled_only: Only return enabled rules
        device_id: Filter by device ID
    """
    try:
        rule_repo = AlertRuleRepository(db)

        if enabled_only:
            rules = await rule_repo.get_enabled_rules()
        elif device_id:
            rules = await rule_repo.get_rules_by_device(device_id)
        else:
            rules = await rule_repo.get_all(skip=skip, limit=limit)

        return APIResponse(
            success=True,
            message=f"Retrieved {len(rules)} alert rules",
            data=[AlertRuleResponse.model_validate(rule) for rule in rules],
        )

    except Exception as e:
        logger.error(f"Failed to list alert rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list alert rules: {str(e)}",
        ) from e


@router.get("/rules/{rule_id}", response_model=APIResponse[AlertRuleResponse])
async def get_alert_rule(
    rule_id: int, db: AsyncSession = Depends(get_db)
) -> APIResponse[AlertRuleResponse]:
    """Get a specific alert rule."""
    try:
        rule_repo = AlertRuleRepository(db)
        rule = await rule_repo.get(rule_id)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert rule {rule_id} not found",
            )

        return APIResponse(
            success=True,
            message="Alert rule retrieved successfully",
            data=AlertRuleResponse.model_validate(rule),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert rule: {str(e)}",
        ) from e


@router.put("/rules/{rule_id}", response_model=APIResponse[AlertRuleResponse])
async def update_alert_rule(
    rule_id: int, rule_data: AlertRuleUpdate, db: AsyncSession = Depends(get_db)
) -> APIResponse[AlertRuleResponse]:
    """Update an alert rule."""
    try:
        rule_repo = AlertRuleRepository(db)

        # Check if rule exists
        rule = await rule_repo.get(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert rule {rule_id} not found",
            )

        # Update rule
        update_data = rule_data.model_dump(exclude_unset=True)
        updated_rule = await rule_repo.update(rule_id, update_data)

        return APIResponse(
            success=True,
            message="Alert rule updated successfully",
            data=AlertRuleResponse.model_validate(updated_rule),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert rule: {str(e)}",
        ) from e


@router.delete(
    "/rules/{rule_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_alert_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> APIResponse[None]:
    """Delete an alert rule."""
    try:
        rule_repo = AlertRuleRepository(db)

        # Check if rule exists
        rule = await rule_repo.get(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert rule {rule_id} not found",
            )

        # Delete rule
        await rule_repo.delete(rule_id)

        return APIResponse(success=True, message="Alert rule deleted successfully", data=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert rule: {str(e)}",
        ) from e


@router.post("/rules/{rule_id}/test", response_model=APIResponse[dict])
async def test_alert_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> APIResponse[dict]:
    """Test an alert rule without triggering actual alerts."""
    try:
        alert_service = AlertService(db)
        results = await alert_service.test_rule(rule_id)

        return APIResponse(
            success=True, message="Alert rule tested successfully", data=results
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to test alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test alert rule: {str(e)}",
        ) from e


# Alert Endpoints


@router.get("/", response_model=APIResponse[list[AlertResponse]])
async def list_alerts(
    skip: int = 0,
    limit: int = 100,
    status_filter: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    device_id: int | None = None,
    rule_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[AlertResponse]]:
    """
    List alerts with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        status_filter: Filter by alert status
        severity: Filter by severity
        device_id: Filter by device ID
        rule_id: Filter by rule ID
        start_date: Filter by start date
        end_date: Filter by end date
    """
    try:
        alert_repo = AlertRepository(db)

        # Apply filters
        if status_filter:
            alerts = await alert_repo.get_by_status(status_filter, skip, limit)
        elif severity:
            alerts = await alert_repo.get_by_severity(severity, skip, limit)
        elif device_id:
            alerts = await alert_repo.get_by_device(device_id, skip, limit)
        elif rule_id:
            alerts = await alert_repo.get_by_rule(rule_id, skip, limit)
        elif start_date and end_date:
            alerts = await alert_repo.get_by_date_range(start_date, end_date, skip, limit)
        else:
            alerts = await alert_repo.get_all(skip=skip, limit=limit)

        return APIResponse(
            success=True,
            message=f"Retrieved {len(alerts)} alerts",
            data=[AlertResponse.model_validate(alert) for alert in alerts],
        )

    except Exception as e:
        logger.error(f"Failed to list alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list alerts: {str(e)}",
        ) from e


@router.get("/active", response_model=APIResponse[list[AlertResponse]])
async def list_active_alerts(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> APIResponse[list[AlertResponse]]:
    """List all active alerts."""
    try:
        alert_repo = AlertRepository(db)
        alerts = await alert_repo.get_active_alerts(skip, limit)

        return APIResponse(
            success=True,
            message=f"Retrieved {len(alerts)} active alerts",
            data=[AlertResponse.model_validate(alert) for alert in alerts],
        )

    except Exception as e:
        logger.error(f"Failed to list active alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list active alerts: {str(e)}",
        ) from e


@router.get("/recent", response_model=APIResponse[list[AlertResponse]])
async def list_recent_alerts(
    hours: int = 24, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> APIResponse[list[AlertResponse]]:
    """
    List recent alerts.

    Args:
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of alerts to return
    """
    try:
        alert_repo = AlertRepository(db)
        alerts = await alert_repo.get_recent_alerts(hours, limit)

        return APIResponse(
            success=True,
            message=f"Retrieved {len(alerts)} recent alerts",
            data=[AlertResponse.model_validate(alert) for alert in alerts],
        )

    except Exception as e:
        logger.error(f"Failed to list recent alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list recent alerts: {str(e)}",
        ) from e


@router.get("/{alert_id}", response_model=APIResponse[AlertResponse])
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> APIResponse[AlertResponse]:
    """Get a specific alert."""
    try:
        alert_repo = AlertRepository(db)
        alert = await alert_repo.get(alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found",
            )

        return APIResponse(
            success=True,
            message="Alert retrieved successfully",
            data=AlertResponse.model_validate(alert),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert: {str(e)}",
        ) from e


@router.put("/{alert_id}/status", response_model=APIResponse[AlertResponse])
async def update_alert_status(
    alert_id: int, status_update: AlertUpdateStatus, db: AsyncSession = Depends(get_db)
) -> APIResponse[AlertResponse]:
    """Update alert status (acknowledge, resolve, or snooze)."""
    try:
        alert_repo = AlertRepository(db)

        # Check if alert exists
        alert = await alert_repo.get(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found",
            )

        # Update status based on action
        if status_update.status == AlertStatus.ACKNOWLEDGED:
            updated_alert = await alert_repo.acknowledge_alert(alert_id)
        elif status_update.status == AlertStatus.RESOLVED:
            updated_alert = await alert_repo.resolve_alert(alert_id)
        elif status_update.status == AlertStatus.SNOOZED:
            if not status_update.snooze_minutes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="snooze_minutes required when status is SNOOZED",
                )
            updated_alert = await alert_repo.snooze_alert(alert_id, status_update.snooze_minutes)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_update.status}",
            )

        return APIResponse(
            success=True,
            message=f"Alert status updated to {status_update.status.value}",
            data=AlertResponse.model_validate(updated_alert),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id} status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert status: {str(e)}",
        ) from e


@router.get("/statistics/summary", response_model=APIResponse[AlertStatistics])
async def get_alert_statistics(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AlertStatistics]:
    """Get alert statistics."""
    try:
        alert_repo = AlertRepository(db)
        stats = await alert_repo.get_alert_statistics()

        return APIResponse(
            success=True,
            message="Alert statistics retrieved successfully",
            data=AlertStatistics.model_validate(stats),
        )

    except Exception as e:
        logger.error(f"Failed to get alert statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert statistics: {str(e)}",
        ) from e
