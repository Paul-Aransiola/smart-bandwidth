"""
API routes for bandwidth control operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import BandwidthControlException
from src.repositories.device_repository import (
    BlockHistoryRepository,
    DeviceRepository,
)
from src.schemas.device import (
    BlockDeviceRequest,
    BlockHistoryResponse,
    DeviceResponse,
    ThrottleDeviceRequest,
)
from src.schemas.response import error_response, success_response
from src.services.bandwidth_controller import BandwidthController
from src.services.websocket_manager import manager as ws_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/block/{ip_address}",
    status_code=status.HTTP_200_OK,
    summary="Block a device",
    description="Block network access for a specific device by IP address using iptables.",
    responses={
        200: {"description": "Device successfully blocked"},
        404: {"description": "Device not found"},
        500: {"description": "Failed to block device"},
    },
)
async def block_device(
    ip_address: str,
    request: BlockDeviceRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Block a device by IP address.

    This endpoint uses iptables to block all network traffic from the specified device.
    Requires root/admin privileges to execute iptables commands.

    Args:
        ip_address: The IP address of the device to block
        request: Request body containing optional reason for blocking
        db: Database session

    Returns:
        Updated device information with blocked status

    Raises:
        HTTPException: If device not found or blocking fails
    """
    logger.info(f"Attempting to block device: {ip_address}")

    # Get repositories
    device_repo = DeviceRepository(db)
    history_repo = BlockHistoryRepository(db)

    # Find device
    device = await device_repo.get_by_ip(ip_address)
    if not device:
        logger.warning(f"Device not found for IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with IP {ip_address} not found",
        )

    # Check if already blocked
    if device.is_blocked:
        logger.info(f"Device {ip_address} is already blocked")
        return success_response(
            data=DeviceResponse.model_validate(device).model_dump(),
            message=f"Device {ip_address} is already blocked",
        )

    # Execute blocking
    controller = BandwidthController()
    try:
        block_success = await controller.block_device(ip_address)
        if not block_success:
            raise BandwidthControlException("Failed to block device")

        # Update device status
        device.is_blocked = True
        device.status = "blocked"
        await device_repo.update(device)

        # Record in history
        from src.models.device import BlockHistory

        history = BlockHistory(
            device_id=device.id,
            action="block",
            reason=request.reason,
        )
        await history_repo.create(history)

        logger.info(f"Successfully blocked device: {ip_address}")

        # Broadcast WebSocket update
        device_data = DeviceResponse.model_validate(device).model_dump()
        await ws_manager.broadcast_device_update(device_data, "device_blocked")

        return success_response(
            data=device_data,
            message=f"Device {ip_address} blocked successfully",
        )

    except BandwidthControlException as e:
        logger.error(f"Failed to block device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error blocking device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.post(
    "/unblock/{ip_address}",
    status_code=status.HTTP_200_OK,
    summary="Unblock a device",
    description="Restore network access for a blocked device by IP address.",
    responses={
        200: {"description": "Device successfully unblocked"},
        404: {"description": "Device not found"},
        500: {"description": "Failed to unblock device"},
    },
)
async def unblock_device(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Unblock a device by IP address.

    This endpoint removes iptables rules blocking the specified device.
    Requires root/admin privileges to execute iptables commands.

    Args:
        ip_address: The IP address of the device to unblock
        db: Database session

    Returns:
        Updated device information with unblocked status

    Raises:
        HTTPException: If device not found or unblocking fails
    """
    logger.info(f"Attempting to unblock device: {ip_address}")

    # Get repositories
    device_repo = DeviceRepository(db)
    history_repo = BlockHistoryRepository(db)

    # Find device
    device = await device_repo.get_by_ip(ip_address)
    if not device:
        logger.warning(f"Device not found for IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with IP {ip_address} not found",
        )

    # Check if not blocked
    if not device.is_blocked:
        logger.info(f"Device {ip_address} is not blocked")
        return success_response(
            data=DeviceResponse.model_validate(device).model_dump(),
            message=f"Device {ip_address} is not blocked",
        )

    # Execute unblocking
    controller = BandwidthController()
    try:
        unblock_success = await controller.unblock_device(ip_address)
        if not unblock_success:
            raise BandwidthControlException("Failed to unblock device")

        # Update device status
        device.is_blocked = False
        device.status = "active" if not device.is_throttled else "throttled"
        await device_repo.update(device)

        # Record in history
        from src.models.device import BlockHistory

        history = BlockHistory(
            device_id=device.id,
            action="unblock",
        )
        await history_repo.create(history)

        logger.info(f"Successfully unblocked device: {ip_address}")

        # Broadcast WebSocket update
        device_data = DeviceResponse.model_validate(device).model_dump()
        await ws_manager.broadcast_device_update(device_data, "device_unblocked")

        return success_response(
            data=device_data,
            message=f"Device {ip_address} unblocked successfully",
        )

    except BandwidthControlException as e:
        logger.error(f"Failed to unblock device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock device: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error unblocking device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.post(
    "/throttle/{ip_address}",
    status_code=status.HTTP_200_OK,
    summary="Throttle a device",
    description="Limit bandwidth for a specific device by IP address using traffic control (tc).",
    responses={
        200: {"description": "Device successfully throttled"},
        404: {"description": "Device not found"},
        500: {"description": "Failed to throttle device"},
    },
)
async def throttle_device(
    ip_address: str,
    request: ThrottleDeviceRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Throttle a device by IP address.

    This endpoint uses Linux tc (traffic control) to limit bandwidth for the specified device.
    Requires root/admin privileges to execute tc commands.

    Args:
        ip_address: The IP address of the device to throttle
        request: Request body containing throttle limit in Mbps and optional reason
        db: Database session

    Returns:
        Updated device information with throttled status

    Raises:
        HTTPException: If device not found or throttling fails
    """
    logger.info(f"Attempting to throttle device: {ip_address} to {request.limit_mbps} Mbps")

    # Get repositories
    device_repo = DeviceRepository(db)
    history_repo = BlockHistoryRepository(db)

    # Find device
    device = await device_repo.get_by_ip(ip_address)
    if not device:
        logger.warning(f"Device not found for IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with IP {ip_address} not found",
        )

    # Check if blocked
    if device.is_blocked:
        logger.warning(f"Cannot throttle blocked device: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot throttle a blocked device. Unblock it first.",
        )

    # Execute throttling
    controller = BandwidthController()
    try:
        success = await controller.throttle_device(ip_address, request.limit_mbps)
        if not success:
            raise BandwidthControlException("Failed to throttle device")

        # Update device status
        device.is_throttled = True
        device.throttle_limit_mbps = request.limit_mbps
        device.status = "throttled"
        await device_repo.update(device)

        # Record in history
        from src.models.device import BlockHistory

        history = BlockHistory(
            device_id=device.id,
            action="throttle",
            throttle_limit_mbps=request.limit_mbps,
            reason=request.reason,
        )
        await history_repo.create(history)

        logger.info(f"Successfully throttled device: {ip_address} to {request.limit_mbps} Mbps")

        # Broadcast WebSocket update
        device_data = DeviceResponse.model_validate(device).model_dump()
        await ws_manager.broadcast_device_update(device_data, "device_throttled")

        return success_response(
            data=device_data,
            message=f"Device {ip_address} throttled to {request.limit_mbps} Mbps",
        )

    except BandwidthControlException as e:
        logger.error(f"Failed to throttle device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to throttle device: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error throttling device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.post(
    "/unthrottle/{ip_address}",
    status_code=status.HTTP_200_OK,
    summary="Remove throttle from device",
    description="Remove bandwidth limit from a throttled device by IP address.",
    responses={
        200: {"description": "Device throttle successfully removed"},
        404: {"description": "Device not found"},
        500: {"description": "Failed to remove throttle"},
    },
)
async def unthrottle_device(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Remove throttle from a device by IP address.

    This endpoint removes tc (traffic control) rules limiting bandwidth for the specified device.
    Requires root/admin privileges to execute tc commands.

    Args:
        ip_address: The IP address of the device to unthrottle
        db: Database session

    Returns:
        Updated device information with unthrottled status

    Raises:
        HTTPException: If device not found or unthrottling fails
    """
    logger.info(f"Attempting to unthrottle device: {ip_address}")

    # Get repositories
    device_repo = DeviceRepository(db)
    history_repo = BlockHistoryRepository(db)

    # Find device
    device = await device_repo.get_by_ip(ip_address)
    if not device:
        logger.warning(f"Device not found for IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with IP {ip_address} not found",
        )

    # Check if not throttled
    if not device.is_throttled:
        logger.info(f"Device {ip_address} is not throttled")
        return success_response(
            data=DeviceResponse.model_validate(device).model_dump(),
            message=f"Device {ip_address} is not throttled",
        )

    # Execute unthrottling
    controller = BandwidthController()
    try:
        unthrottle_success = await controller.unthrottle_device(ip_address)
        if not unthrottle_success:
            raise BandwidthControlException("Failed to remove throttle from device")

        # Update device status
        device.is_throttled = False
        device.throttle_limit_mbps = None
        device.status = "active" if not device.is_blocked else "blocked"
        await device_repo.update(device)

        # Record in history
        from src.models.device import BlockHistory

        history = BlockHistory(
            device_id=device.id,
            action="unthrottle",
        )
        await history_repo.create(history)

        logger.info(f"Successfully removed throttle from device: {ip_address}")

        # Broadcast WebSocket update
        device_data = DeviceResponse.model_validate(device).model_dump()
        await ws_manager.broadcast_device_update(device_data, "device_unthrottled")

        return success_response(
            data=device_data,
            message=f"Throttle removed from device {ip_address}",
        )

    except BandwidthControlException as e:
        logger.error(f"Failed to unthrottle device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove throttle: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error unthrottling device {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.get(
    "/history/{ip_address}",
    status_code=status.HTTP_200_OK,
    summary="Get device control history",
    description="Retrieve the history of control actions for a specific device.",
    responses={
        200: {"description": "History retrieved successfully"},
        404: {"description": "Device not found"},
    },
)
async def get_device_history(
    ip_address: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Get control history for a device.

    Retrieves the history of all control actions (block, unblock, throttle, unthrottle)
    performed on the specified device.

    Args:
        ip_address: The IP address of the device
        limit: Maximum number of history records to return (default: 50)
        db: Database session

    Returns:
        List of control history records

    Raises:
        HTTPException: If device not found
    """
    logger.info(f"Retrieving control history for device: {ip_address}")

    # Get repositories
    device_repo = DeviceRepository(db)
    history_repo = BlockHistoryRepository(db)

    # Find device
    device = await device_repo.get_by_ip(ip_address)
    if not device:
        logger.warning(f"Device not found for IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with IP {ip_address} not found",
        )

    # Get history
    history = await history_repo.get_device_history(device.id, limit=limit)
    logger.info(f"Retrieved {len(history)} history records for device: {ip_address}")

    return success_response(
        data=[BlockHistoryResponse.model_validate(h).model_dump() for h in history],
        message=f"Retrieved {len(history)} history records for device {ip_address}",
    )
