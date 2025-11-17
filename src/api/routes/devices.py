"""Device management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import DeviceAlreadyExistsException, DeviceNotFoundException
from src.repositories.device_repository import DeviceRepository
from src.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from src.schemas.response import paginated_response, success_response
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/devices")
async def list_devices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all devices.

    Returns paginated list of all monitored devices with their current status
    and bandwidth usage information.
    """
    repo = DeviceRepository(db)
    devices = await repo.get_all(skip=skip, limit=limit)

    # Get total count (in real app, would be a separate query)
    # For now, assume total equals returned count if less than limit
    total = len(devices) if len(devices) < limit else skip + len(devices) + 1

    return paginated_response(
        data=[DeviceResponse.model_validate(d).model_dump() for d in devices],
        total=total,
        skip=skip,
        limit=limit,
        message=f"Retrieved {len(devices)} devices",
    )


@router.get("/devices/{device_id}")
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get device by ID.

    Returns detailed information about a specific device.
    """
    repo = DeviceRepository(db)
    device = await repo.get_by_id(device_id)

    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    return success_response(
        data=DeviceResponse.model_validate(device).model_dump(),
        message=f"Device {device_id} retrieved successfully",
    )


@router.get("/devices/ip/{ip_address}")
async def get_device_by_ip(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get device by IP address.

    Returns device information for the specified IP address.
    """
    repo = DeviceRepository(db)
    device = await repo.get_by_ip(ip_address)

    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip_address} not found")

    return success_response(
        data=DeviceResponse.model_validate(device).model_dump(),
        message=f"Device {ip_address} retrieved successfully",
    )


@router.post("/devices", status_code=201)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new device.

    Manually register a device in the system.
    """
    repo = DeviceRepository(db)

    # Check if device already exists
    existing = await repo.get_by_ip(device_data.ip_address)
    if existing:
        raise DeviceAlreadyExistsException(device_data.ip_address)

    from src.models.device import Device

    device = Device(**device_data.model_dump())
    created_device = await repo.create(device)

    logger.info(f"Created device: {created_device.ip_address}")
    return success_response(
        data=DeviceResponse.model_validate(created_device).model_dump(),
        message=f"Device {created_device.ip_address} created successfully",
    )


@router.patch("/devices/{device_id}")
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update device information.

    Update device details such as hostname, device name, or notes.
    """
    repo = DeviceRepository(db)
    device = await repo.get_by_id(device_id)

    if not device:
        raise DeviceNotFoundException(str(device_id))

    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    updated_device = await repo.update(device)
    logger.info(f"Updated device: {device_id}")

    return success_response(
        data=DeviceResponse.model_validate(updated_device).model_dump(),
        message=f"Device {device_id} updated successfully",
    )


@router.delete("/devices/{device_id}", status_code=200)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a device.

    Remove a device from the system.
    """
    repo = DeviceRepository(db)
    device = await repo.get_by_id(device_id)

    if not device:
        raise DeviceNotFoundException(str(device_id))

    await repo.delete(device)
    logger.info(f"Deleted device: {device_id}")

    return success_response(
        data=None,
        message=f"Device {device_id} deleted successfully",
    )
