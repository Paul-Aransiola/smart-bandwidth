"""Device management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.core.database import get_db
from src.core.exceptions import DeviceAlreadyExistsException, DeviceNotFoundException
from src.repositories.device_repository import DeviceRepository
from src.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from src.schemas.response import paginated_response, success_response
from src.services.network_scanner import get_network_scanner
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


@router.post("/devices/scan/network", status_code=202)
async def scan_network(
    background_tasks: BackgroundTasks,
    use_ping: bool = Query(False, description="Perform ping sweep (slower but more thorough)"),
    auto_add: bool = Query(False, description="Automatically add discovered devices to database"),
    db: AsyncSession = Depends(get_db),
):
    """
    Scan the local network for devices.

    Performs network discovery using multiple techniques:
    - ARP table scanning (fast, cached data)
    - Active connection monitoring (current connections)
    - Optional: Ping sweep (thorough but slower)

    Args:
        use_ping: If True, performs ping sweep for more thorough discovery
        auto_add: If True, automatically adds discovered devices to database

    Returns:
        Scan status and initial results
    """
    scanner = get_network_scanner()

    # Get quick results from ARP table immediately
    arp_devices = scanner.scan_arp_table()
    conn_devices = scanner.scan_active_connections()

    # Merge quick results
    quick_results = {**arp_devices}
    for ip, device in conn_devices.items():
        if ip in quick_results:
            quick_results[ip].update(
                {
                    k: v
                    for k, v in device.items()
                    if v is not None
                    and (k not in quick_results[ip] or quick_results[ip][k] is None)
                }
            )
        else:
            quick_results[ip] = device

    async def perform_full_scan():
        """Background task for full network scan."""
        try:
            logger.info("Starting background network scan")
            all_devices = await scanner.scan_all_networks(
                use_ping=use_ping, include_connections=True
            )

            if auto_add:
                # Auto-add discovered devices to database
                repo = DeviceRepository(db)
                added_count = 0
                skipped_count = 0
                error_count = 0

                logger.info(
                    f"Background scan found {len(all_devices)} devices, attempting to auto-add"
                )

                for ip, device_info in all_devices.items():
                    try:
                        existing = await repo.get_by_ip(ip)
                        if existing:
                            logger.debug(f"Device {ip} already exists in database")
                            skipped_count += 1
                            continue

                        from src.models.device import Device, DeviceStatus

                        # Skip if no MAC address
                        mac = device_info.get("mac_address")
                        if not mac:
                            logger.warning(
                                f"Skipping device {ip}: No MAC address found in device_info: {device_info}"
                            )
                            skipped_count += 1
                            continue

                        # Classify device type
                        device_type = scanner.classify_device_type(device_info)

                        # Generate a meaningful device name
                        hostname = device_info.get("hostname")
                        if hostname and hostname != "?" and not hostname.startswith("_gateway"):
                            device_name = hostname
                        else:
                            # Use MAC vendor or device type for better naming
                            if mac:
                                # Extract first 3 octets for vendor lookup
                                vendor_prefix = mac.replace(":", "")[:6].upper()
                                # Common vendor mappings (partial list)
                                vendor_map = {
                                    "F4939": "Belkin",
                                    "001EC": "Apple",
                                    "00166": "Cisco",
                                    "D85D4": "ASUSTek",
                                    "7C2F8": "Google",
                                    "B827E": "Raspberry Pi",
                                    "DCA63": "Raspberry Pi",
                                    "E45F0": "Raspberry Pi",
                                }
                                vendor = next(
                                    (
                                        v
                                        for k, v in vendor_map.items()
                                        if vendor_prefix.startswith(k)
                                    ),
                                    None,
                                )
                                if vendor:
                                    device_name = f"{vendor} Device ({ip})"
                                else:
                                    device_name = f"{device_type.replace('_', ' ').title()} ({ip})"
                            else:
                                device_name = f"Device-{ip}"

                        new_device = Device(
                            ip_address=ip,
                            mac_address=mac,
                            hostname=hostname,
                            device_name=device_name,
                            device_type=device_type,
                            status=DeviceStatus.ACTIVE,
                            first_seen=datetime.now(),
                            last_seen=device_info.get("last_seen", datetime.now()),
                        )

                        await repo.create(new_device)
                        added_count += 1
                        logger.info(f"Auto-added device: {ip} (MAC: {mac}, Type: {device_type})")
                    except Exception as e:
                        logger.error(f"Error auto-adding device {ip}: {e}", exc_info=True)
                        error_count += 1

                await db.commit()
                logger.info(
                    f"Background scan complete: added={added_count}, skipped={skipped_count}, errors={error_count}"
                )

        except Exception as e:
            logger.error(f"Error in background network scan: {e}")

    # Schedule full scan in background if ping is requested
    if use_ping:
        background_tasks.add_task(perform_full_scan)

    # For quick scans, add devices immediately if auto_add is enabled
    elif auto_add:
        repo = DeviceRepository(db)
        added_count = 0
        skipped_count = 0
        error_count = 0

        logger.info(f"Quick scan found {len(quick_results)} devices, attempting to auto-add")

        for ip, device_info in quick_results.items():
            try:
                # Skip multicast and link-local addresses
                if ip.startswith("224.") or ip.startswith("169.254."):
                    logger.debug(f"Skipping multicast/link-local IP: {ip}")
                    skipped_count += 1
                    continue

                # Skip if no MAC address
                mac = device_info.get("mac_address")
                if not mac:
                    logger.warning(
                        f"Skipping device {ip}: No MAC address found in device_info: {device_info}"
                    )
                    skipped_count += 1
                    continue

                existing = await repo.get_by_ip(ip)
                if existing:
                    logger.debug(f"Device {ip} already exists in database")
                    skipped_count += 1
                    continue

                from src.models.device import Device, DeviceStatus

                # Classify device type
                device_type = scanner.classify_device_type(device_info)

                # Generate a meaningful device name
                hostname = device_info.get("hostname")
                if hostname and hostname != "?" and not hostname.startswith("_gateway"):
                    device_name = hostname
                else:
                    # Use MAC vendor or device type for better naming
                    mac = device_info.get("mac_address", "")
                    if mac:
                        # Extract first 3 octets for vendor lookup
                        vendor_prefix = mac.replace(":", "")[:6].upper()
                        # Common vendor mappings (partial list)
                        vendor_map = {
                            "F4939": "Belkin",
                            "001EC": "Apple",
                            "00166": "Cisco",
                            "D85D4": "ASUSTek",
                            "7C2F8": "Google",
                            "B827E": "Raspberry Pi",
                            "DCA63": "Raspberry Pi",
                            "E45F0": "Raspberry Pi",
                        }
                        vendor = next(
                            (v for k, v in vendor_map.items() if vendor_prefix.startswith(k)), None
                        )
                        if vendor:
                            device_name = f"{vendor} Device ({ip})"
                        else:
                            device_name = f"{device_type.replace('_', ' ').title()} ({ip})"
                    else:
                        device_name = f"Device-{ip}"

                new_device = Device(
                    ip_address=ip,
                    mac_address=mac,
                    hostname=hostname,
                    device_name=device_name,
                    device_type=device_type,
                    status=DeviceStatus.ACTIVE,
                    first_seen=datetime.now(),
                    last_seen=device_info.get("last_seen", datetime.now()),
                )

                await repo.create(new_device)
                added_count += 1
                logger.info(f"Auto-added device: {ip} (MAC: {mac}, Type: {device_type})")
            except Exception as e:
                logger.error(f"Error auto-adding device {ip}: {e}", exc_info=True)
                error_count += 1

        await db.commit()
        logger.info(
            f"Quick scan complete: added={added_count}, skipped={skipped_count}, errors={error_count}"
        )

    return success_response(
        data={
            "devices_found": len(quick_results),
            "devices": [
                {
                    "ip_address": ip,
                    "mac_address": info.get("mac_address"),
                    "hostname": info.get("hostname"),
                    "discovery_method": info.get("discovery_method"),
                    "last_seen": info.get("last_seen").isoformat()
                    if info.get("last_seen")
                    else None,
                }
                for ip, info in quick_results.items()
            ],
            "scan_status": "in_progress" if use_ping else "completed",
            "full_scan_running": use_ping,
        },
        message=f"Found {len(quick_results)} devices. "
        + ("Full scan running in background." if use_ping else "Quick scan completed."),
    )


@router.get("/devices/scan/status")
async def get_scan_status():
    """
    Get the status of the last network scan.

    Returns information about the last scan including timestamp
    and number of devices discovered.
    """
    scanner = get_network_scanner()

    return success_response(
        data={
            "last_scan_time": scanner.last_scan_time.isoformat()
            if scanner.last_scan_time
            else None,
            "devices_discovered": len(scanner.discovered_devices),
            "devices": [
                {
                    "ip_address": ip,
                    "mac_address": info.get("mac_address"),
                    "hostname": info.get("hostname"),
                    "discovery_method": info.get("discovery_method"),
                }
                for ip, info in scanner.discovered_devices.items()
            ],
        },
        message="Scan status retrieved successfully",
    )


@router.get("/devices/network/ranges")
async def get_network_ranges():
    """
    Get detected local network ranges.

    Returns the network ranges that would be scanned,
    based on the system's network interfaces.
    """
    scanner = get_network_scanner()
    ranges = scanner.get_local_network_ranges()

    return success_response(
        data={
            "network_ranges": ranges,
            "total_ranges": len(ranges),
        },
        message=f"Found {len(ranges)} local network range(s)",
    )
