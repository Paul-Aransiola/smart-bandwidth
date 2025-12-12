"""
Advanced bandwidth control API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user, require_admin
from src.core.database import get_db

# User model stub - TODO: implement auth
from src.repositories.advanced_controls_repository import (
    BandwidthQuotaRepository,
    QoSPolicyRepository,
    ThrottleScheduleRepository,
)
from src.schemas.advanced_controls import (
    BandwidthQuotaCreate,
    BandwidthQuotaResponse,
    BandwidthQuotaUpdate,
    QoSPolicyCreate,
    QoSPolicyResponse,
    QoSPolicyUpdate,
    ThrottleScheduleCreate,
    ThrottleScheduleResponse,
    ThrottleScheduleUpdate,
)
from src.schemas.response import success_response
from src.utils.logger import get_logger

router = APIRouter(prefix="/advanced-controls")
logger = get_logger(__name__)


# Bandwidth Quota endpoints
@router.post(
    "/quotas",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create bandwidth quota",
)
async def create_quota(
    quota_data: BandwidthQuotaCreate,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new bandwidth quota.

    Requires admin privileges. Quotas can be set per device or globally.
    """
    try:
        repo = BandwidthQuotaRepository(db)

        quota_dict = quota_data.model_dump()
        quota_dict["used_bytes"] = 0
        quota_dict["is_active"] = True

        quota = await repo.create(quota_dict)
        await db.commit()
        return success_response(
            data=BandwidthQuotaResponse.model_validate(quota).model_dump(),
            message="Bandwidth quota created successfully",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bandwidth quota",
        ) from e


@router.get("/quotas", response_model=dict, summary="List bandwidth quotas")
async def list_quotas(
    device_id: int | None = Query(None, description="Filter by device ID"),
    active_only: bool = Query(True, description="Show only active quotas"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all bandwidth quotas with optional filters."""
    try:
        repo = BandwidthQuotaRepository(db)

        if device_id:
            quotas = await repo.get_by_device(device_id)
            if active_only:
                quotas = [q for q in quotas if q.is_active]
        elif active_only:
            quotas = await repo.get_active_quotas()
        else:
            quotas = await repo.get_all(skip=0, limit=1000)

        return success_response(
            data=[BandwidthQuotaResponse.model_validate(q).model_dump() for q in quotas],
            message=f"Retrieved {len(quotas)} quotas",
        )
    except Exception as e:
        logger.error(f"Error listing quotas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quotas",
        ) from e


@router.put("/quotas/{quota_id}", response_model=dict, summary="Update bandwidth quota")
async def update_quota(
    quota_id: int,
    quota_data: BandwidthQuotaUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing bandwidth quota."""
    try:
        repo = BandwidthQuotaRepository(db)

        updated_quota = await repo.update(quota_id, quota_data.model_dump(exclude_unset=True))
        if not updated_quota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota not found",
            )

        await db.commit()
        return success_response(
            data=BandwidthQuotaResponse.model_validate(updated_quota).model_dump(),
            message="Quota updated successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quota",
        ) from e


@router.post("/quotas/{quota_id}/reset", response_model=dict, summary="Reset bandwidth quota")
async def reset_quota(
    quota_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset a quota's used bytes to zero."""
    try:
        repo = BandwidthQuotaRepository(db)

        quota = await repo.reset_quota(quota_id)
        if not quota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota not found",
            )

        return success_response(
            data=BandwidthQuotaResponse.model_validate(quota).model_dump(),
            message="Quota reset successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resetting quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset quota",
        ) from e


@router.delete("/quotas/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota(
    quota_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a bandwidth quota."""
    try:
        repo = BandwidthQuotaRepository(db)

        success = await repo.delete(quota_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quota not found",
            )

        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quota",
        ) from e


# QoS Policy endpoints
@router.post(
    "/qos-policies",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create QoS policy",
)
async def create_qos_policy(
    policy_data: QoSPolicyCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new QoS policy for traffic prioritization.

    Requires admin privileges.
    """
    try:
        repo = QoSPolicyRepository(db)

        # Check if policy name already exists
        existing = await repo.get_by_name(policy_data.policy_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Policy with this name already exists",
            )

        policy_dict = policy_data.model_dump()
        policy_dict["is_enabled"] = True

        policy = await repo.create(policy_dict)
        await db.commit()
        return success_response(
            data=QoSPolicyResponse.model_validate(policy).model_dump(),
            message="QoS policy created successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating QoS policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create QoS policy",
        ) from e


@router.get("/qos-policies", response_model=dict, summary="List QoS policies")
async def list_qos_policies(
    priority: str | None = Query(None, description="Filter by priority"),
    enabled_only: bool = Query(True, description="Show only enabled policies"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all QoS policies with optional filters."""
    try:
        repo = QoSPolicyRepository(db)

        if priority:
            policies = await repo.get_by_priority(priority)
        elif enabled_only:
            policies = await repo.get_enabled_policies()
        else:
            policies = await repo.get_all(skip=0, limit=1000)

        return success_response(
            data=[QoSPolicyResponse.model_validate(p).model_dump() for p in policies],
            message=f"Retrieved {len(policies)} policies",
        )
    except Exception as e:
        logger.error(f"Error listing QoS policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list QoS policies",
        ) from e


@router.put("/qos-policies/{policy_id}", response_model=dict, summary="Update QoS policy")
async def update_qos_policy(
    policy_id: int,
    policy_data: QoSPolicyUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing QoS policy."""
    try:
        repo = QoSPolicyRepository(db)

        updated_policy = await repo.update(policy_id, policy_data.model_dump(exclude_unset=True))
        if not updated_policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )

        await db.commit()
        return success_response(
            data=QoSPolicyResponse.model_validate(updated_policy).model_dump(),
            message="QoS policy updated successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating QoS policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update QoS policy",
        ) from e


@router.delete("/qos-policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qos_policy(
    policy_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a QoS policy."""
    try:
        repo = QoSPolicyRepository(db)

        success = await repo.delete(policy_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )

        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting QoS policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete QoS policy",
        ) from e


# Throttle Schedule endpoints
@router.post(
    "/schedules",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create throttle schedule",
)
async def create_schedule(
    schedule_data: ThrottleScheduleCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new throttle schedule.

    Requires admin privileges. Schedules allow automatic bandwidth throttling
    based on time of day.
    """
    try:
        repo = ThrottleScheduleRepository(db)

        schedule_dict = schedule_data.model_dump()
        schedule_dict["is_enabled"] = True

        schedule = await repo.create(schedule_dict)
        await db.commit()
        return success_response(
            data=ThrottleScheduleResponse.model_validate(schedule).model_dump(),
            message="Throttle schedule created successfully",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create throttle schedule",
        ) from e


@router.get("/schedules", response_model=dict, summary="List throttle schedules")
async def list_schedules(
    device_id: int | None = Query(None, description="Filter by device ID"),
    enabled_only: bool = Query(True, description="Show only enabled schedules"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all throttle schedules with optional filters."""
    try:
        repo = ThrottleScheduleRepository(db)

        if device_id:
            schedules = await repo.get_by_device(device_id)
            if enabled_only:
                schedules = [s for s in schedules if s.is_enabled]
        elif enabled_only:
            schedules = await repo.get_enabled_schedules()
        else:
            schedules = await repo.get_all(skip=0, limit=1000)

        return success_response(
            data=[ThrottleScheduleResponse.model_validate(s).model_dump() for s in schedules],
            message=f"Retrieved {len(schedules)} schedules",
        )
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules",
        ) from e


@router.put("/schedules/{schedule_id}", response_model=dict, summary="Update throttle schedule")
async def update_schedule(
    schedule_id: int,
    schedule_data: ThrottleScheduleUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing throttle schedule."""
    try:
        repo = ThrottleScheduleRepository(db)

        updated_schedule = await repo.update(
            schedule_id, schedule_data.model_dump(exclude_unset=True)
        )
        if not updated_schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )

        await db.commit()
        return success_response(
            data=ThrottleScheduleResponse.model_validate(updated_schedule).model_dump(),
            message="Schedule updated successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule",
        ) from e


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a throttle schedule."""
    try:
        repo = ThrottleScheduleRepository(db)

        success = await repo.delete(schedule_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )

        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule",
        ) from e
