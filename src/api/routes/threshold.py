"""
API routes for bandwidth threshold management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device_repository import DeviceRepository
from src.repositories.advanced_controls_repository import GlobalSettingsRepository
from src.schemas.response import ErrorResponse, success_response
from src.services.threshold_monitor import get_threshold_monitor
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/threshold", tags=["threshold"])

# Type alias for success responses
SuccessResponse = dict


@router.post(
    "/devices/{device_id}/set",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Set bandwidth threshold for device",
    description="Configure bandwidth threshold and auto-deactivation settings for a device",
)
async def set_device_threshold(
    device_id: int,
    threshold_mbps: float,
    auto_deactivate: bool = False,
    time_window_minutes: int = 5,
    session: AsyncSession = Depends(get_db),
):
    """
    Set bandwidth threshold for a device.

    Args:
        device_id: Device ID
        threshold_mbps: Bandwidth threshold in Mbps
        auto_deactivate: Enable auto-deactivation on threshold breach
        time_window_minutes: Time window for threshold evaluation (1-1440 minutes)
        session: Database session

    Returns:
        Success response with updated device info
    """
    try:
        logger.info(
            f"[THRESHOLD-SET] START: device_id={device_id}, threshold={threshold_mbps}, auto_deactivate={auto_deactivate}, time_window={time_window_minutes}"
        )

        if threshold_mbps <= 0:
            logger.error(f"[THRESHOLD-SET] Invalid threshold: {threshold_mbps}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Threshold must be greater than 0 Mbps",
            )

        if not 1 <= time_window_minutes <= 1440:
            logger.error(f"[THRESHOLD-SET] Invalid time window: {time_window_minutes}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time window must be between 1 and 1440 minutes",
            )

        logger.info(f"[THRESHOLD-SET] Creating DeviceRepository")
        device_repo = DeviceRepository(session)

        logger.info(f"[THRESHOLD-SET] Fetching device {device_id}")
        device = await device_repo.get(device_id)

        if not device:
            logger.error(f"[THRESHOLD-SET] Device not found: {device_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found",
            )

        logger.info(f"[THRESHOLD-SET] Updating device {device_id}")
        # Update device threshold settings
        device.bandwidth_threshold_mbps = threshold_mbps
        device.auto_deactivate_on_threshold = auto_deactivate
        device.threshold_time_window_minutes = time_window_minutes

        updated_device = await device_repo.update(device)

        logger.info(
            f"[THRESHOLD-SET] SUCCESS: Threshold set for device {device.ip_address}: "
            f"{threshold_mbps} Mbps, auto_deactivate={auto_deactivate}, "
            f"window={time_window_minutes}min"
        )

        logger.info(f"[THRESHOLD-SET] Creating response")
        response = success_response(
            message=f"Bandwidth threshold configured: {threshold_mbps} Mbps",
            data={
                "device_id": device_id,
                "device_ip": device.ip_address,
                "device_hostname": device.hostname,
                "threshold_mbps": threshold_mbps,
                "auto_deactivate": auto_deactivate,
                "time_window_minutes": time_window_minutes,
            },
        )
        logger.info(f"[THRESHOLD-SET] Returning response")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[THRESHOLD-SET] EXCEPTION: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting threshold: {str(e)}",
        )


@router.delete(
    "/devices/{device_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
    summary="Remove bandwidth threshold",
    description="Remove bandwidth threshold configuration from a device",
)
async def remove_device_threshold(
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Remove bandwidth threshold from a device.

    Args:
        device_id: Device ID
        session: Database session

    Returns:
        Success response
    """
    device_repo = DeviceRepository(session)
    device = await device_repo.get(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    # Clear threshold settings
    device.bandwidth_threshold_mbps = None
    device.auto_deactivate_on_threshold = False
    device.threshold_time_window_minutes = 5

    await device_repo.update(device)

    logger.info(f"Threshold removed from device {device.ip_address}")

    return success_response(
        message="Bandwidth threshold removed",
        data={
            "device_id": device_id,
            "device_ip": device.ip_address,
        },
    )


@router.get(
    "/devices/{device_id}/status",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
    summary="Get threshold status for device",
    description="Get current bandwidth usage and threshold status for a device",
)
async def get_device_threshold_status(
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Get threshold status for a device.

    Args:
        device_id: Device ID
        session: Database session

    Returns:
        Success response with threshold status
    """
    device_repo = DeviceRepository(session)
    device = await device_repo.get(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    # Get current bandwidth usage and threshold check
    threshold_monitor = get_threshold_monitor()
    status_data = await threshold_monitor.check_device_now(device_id)

    return success_response(
        message="Threshold status retrieved",
        data=status_data,
    )


@router.post(
    "/devices/{device_id}/check",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
    summary="Manually check device threshold",
    description="Trigger an immediate threshold check for a device",
)
async def check_device_threshold(
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Manually trigger threshold check for a device.

    Args:
        device_id: Device ID
        session: Database session

    Returns:
        Success response with check results
    """
    device_repo = DeviceRepository(session)
    device = await device_repo.get(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    # Trigger threshold check
    threshold_monitor = get_threshold_monitor()
    result = await threshold_monitor.check_device_now(device_id)

    message = "Threshold check completed"
    if result.get("threshold_breached"):
        message = "⚠️ Bandwidth threshold exceeded!"
    elif not result.get("threshold_configured"):
        message = "No threshold configured for this device"

    return success_response(
        message=message,
        data=result,
    )


@router.get(
    "/devices",
    response_model=dict,
    summary="List devices with thresholds",
    description="Get all devices that have bandwidth thresholds configured",
)
async def list_devices_with_thresholds(
    session: AsyncSession = Depends(get_db),
):
    """
    List all devices with bandwidth thresholds configured.

    Args:
        session: Database session

    Returns:
        Success response with device list
    """
    device_repo = DeviceRepository(session)
    devices = await device_repo.get_devices_with_thresholds()

    devices_data = [
        {
            "device_id": d.id,
            "ip_address": d.ip_address,
            "hostname": d.hostname,
            "status": d.status.value,
            "threshold_mbps": d.bandwidth_threshold_mbps,
            "auto_deactivate": d.auto_deactivate_on_threshold,
            "time_window_minutes": d.threshold_time_window_minutes,
            "breach_count": d.threshold_breach_count,
            "last_breach": d.last_threshold_breach.isoformat() if d.last_threshold_breach else None,
        }
        for d in devices
    ]

    return success_response(
        message=f"Found {len(devices)} devices with thresholds configured",
        data={
            "devices": devices_data,
            "count": len(devices),
        },
    )


@router.post(
    "/devices/{device_id}/reactivate",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Reactivate deactivated device",
    description="Reactivate a device that was auto-deactivated due to threshold breach",
)
async def reactivate_device(
    device_id: int,
    reset_breach_count: bool = False,
    session: AsyncSession = Depends(get_db),
):
    """
    Reactivate a device that was auto-deactivated.

    Args:
        device_id: Device ID
        reset_breach_count: Reset breach count to 0
        session: Database session

    Returns:
        Success response
    """
    from src.models.device import DeviceStatus
    from src.services.bandwidth_controller import BandwidthController

    device_repo = DeviceRepository(session)
    device = await device_repo.get(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    if device.status != DeviceStatus.DEACTIVATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device is not deactivated (current status: {device.status.value})",
        )

    # Unblock device at network level
    bandwidth_controller = BandwidthController()
    await bandwidth_controller.unblock_device(device.ip_address)

    # Update device status
    device.status = DeviceStatus.ACTIVE
    device.is_blocked = False

    if reset_breach_count:
        device.threshold_breach_count = 0

    await device_repo.update(device)

    logger.info(f"Device {device.ip_address} reactivated (reset_breach_count={reset_breach_count})")

    return success_response(
        message=f"Device {device.ip_address} has been reactivated",
        data={
            "device_id": device_id,
            "device_ip": device.ip_address,
            "status": "active",
            "breach_count_reset": reset_breach_count,
        },
    )


@router.get(
    "/global",
    response_model=dict,
    summary="Get global threshold settings",
    description="Retrieve global bandwidth threshold settings that apply to all devices without individual thresholds",
)
async def get_global_threshold(session: AsyncSession = Depends(get_db)):
    """
    Get global threshold settings.

    Returns:
        Success response with global threshold configuration
    """
    settings_repo = GlobalSettingsRepository(session)

    # Get all global threshold settings
    threshold_str = await settings_repo.get_value("global_bandwidth_threshold_mbps")
    auto_deactivate_str = await settings_repo.get_value("global_auto_deactivate_on_threshold")
    time_window_str = await settings_repo.get_value("global_threshold_time_window_minutes")

    # Convert to appropriate types
    threshold = float(threshold_str) if threshold_str else None
    auto_deactivate = auto_deactivate_str == "true" if auto_deactivate_str else False
    time_window = int(time_window_str) if time_window_str else 5

    # Count devices that would use global threshold
    device_repo = DeviceRepository(session)
    devices_with_thresholds = await device_repo.get_devices_with_thresholds()
    all_active = await device_repo.get_all_active()
    devices_using_global = len(
        [d for d in all_active if d.id not in {dev.id for dev in devices_with_thresholds}]
    )

    return success_response(
        message="Global threshold settings retrieved successfully",
        data={
            "threshold_mbps": threshold,
            "auto_deactivate": auto_deactivate,
            "time_window_minutes": time_window,
            "devices_using_global_threshold": devices_using_global,
            "total_active_devices": len(all_active),
        },
    )


@router.post(
    "/global/set",
    response_model=dict,
    responses={400: {"model": ErrorResponse}},
    summary="Set global threshold",
    description="Configure global bandwidth threshold that applies to all devices without individual thresholds",
)
async def set_global_threshold(
    threshold_mbps: float,
    auto_deactivate: bool = False,
    time_window_minutes: int = 5,
    session: AsyncSession = Depends(get_db),
):
    """
    Set global bandwidth threshold.

    Args:
        threshold_mbps: Bandwidth threshold in Mbps
        auto_deactivate: Enable auto-deactivation on threshold breach
        time_window_minutes: Time window for threshold evaluation (1-1440 minutes)
        session: Database session

    Returns:
        Success response with global threshold configuration
    """
    if threshold_mbps <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold must be greater than 0",
        )

    if not 1 <= time_window_minutes <= 1440:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time window must be between 1 and 1440 minutes",
        )

    settings_repo = GlobalSettingsRepository(session)

    # Set global threshold settings
    await settings_repo.set_value(
        "global_bandwidth_threshold_mbps",
        str(threshold_mbps),
        "float",
        "Global bandwidth threshold in Mbps for devices without individual thresholds",
    )
    await settings_repo.set_value(
        "global_auto_deactivate_on_threshold",
        "true" if auto_deactivate else "false",
        "boolean",
        "Auto-deactivate devices when they exceed the global bandwidth threshold",
    )
    await settings_repo.set_value(
        "global_threshold_time_window_minutes",
        str(time_window_minutes),
        "integer",
        "Time window in minutes for global threshold evaluation",
    )

    # Count devices that will use global threshold
    device_repo = DeviceRepository(session)
    devices_with_thresholds = await device_repo.get_devices_with_thresholds()
    all_active = await device_repo.get_all_active()
    devices_using_global = len(
        [d for d in all_active if d.id not in {dev.id for dev in devices_with_thresholds}]
    )

    logger.info(
        f"Global threshold set: {threshold_mbps} Mbps, "
        f"auto_deactivate={auto_deactivate}, time_window={time_window_minutes}min, "
        f"applies to {devices_using_global} devices"
    )

    return success_response(
        message="Global threshold settings updated successfully",
        data={
            "threshold_mbps": threshold_mbps,
            "auto_deactivate": auto_deactivate,
            "time_window_minutes": time_window_minutes,
            "devices_affected": devices_using_global,
            "total_active_devices": len(all_active),
        },
    )


@router.delete(
    "/global",
    response_model=dict,
    summary="Remove global threshold",
    description="Remove global bandwidth threshold settings",
)
async def remove_global_threshold(session: AsyncSession = Depends(get_db)):
    """
    Remove global bandwidth threshold.

    Returns:
        Success response
    """
    settings_repo = GlobalSettingsRepository(session)

    # Count devices before removal
    device_repo = DeviceRepository(session)
    devices_with_thresholds = await device_repo.get_devices_with_thresholds()
    all_active = await device_repo.get_all_active()
    devices_using_global = len(
        [d for d in all_active if d.id not in {dev.id for dev in devices_with_thresholds}]
    )

    # Remove global threshold settings
    await settings_repo.delete_by_key("global_bandwidth_threshold_mbps")
    await settings_repo.delete_by_key("global_auto_deactivate_on_threshold")
    await settings_repo.delete_by_key("global_threshold_time_window_minutes")

    logger.info(f"Global threshold removed, previously applied to {devices_using_global} devices")

    return success_response(
        message="Global threshold settings removed successfully",
        data={
            "devices_previously_affected": devices_using_global,
        },
    )
