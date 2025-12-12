"""
WebSocket endpoints for real-time monitoring.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device_repository import DeviceRepository
from src.services.websocket_manager import manager
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/monitor")
async def websocket_monitor(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time monitoring.

    Clients connect to this endpoint to receive real-time updates about:
    - Device status changes
    - Bandwidth statistics
    - Block/unblock events
    - Throttle events

    Message format:
    ```json
    {
        "type": "device_update|bandwidth_stats|device_list",
        "timestamp": "2025-11-17T10:30:00",
        "data": {...}
    }
    ```
    """
    await manager.connect(websocket)

    try:
        # Send initial device list
        await manager.broadcast_device_list(db)

        # Keep connection alive and handle client messages
        while True:
            # Wait for client messages
            data = await websocket.receive_text()

            # Handle client requests
            if data == "ping":
                await manager.send_personal_message({"type": "pong", "timestamp": "now"}, websocket)
            elif data == "get_devices":
                # Send current device list to this client only
                device_repo = DeviceRepository(db)
                devices = await device_repo.get_all(skip=0, limit=100)
                device_list = [
                    {
                        "ip_address": device.ip_address,
                        "mac_address": device.mac_address,
                        "hostname": device.hostname,
                        "device_name": device.device_name,
                        "device_type": device.device_type,
                        "manufacturer": device.manufacturer,
                        "os_type": device.os_type,
                        "status": device.status.value,
                        "is_blocked": device.is_blocked,
                        "is_throttled": device.is_throttled,
                        "total_bytes_sent": device.total_bytes_sent,
                        "total_bytes_received": device.total_bytes_received,
                    }
                    for device in devices
                ]
                await manager.send_personal_message(
                    {
                        "type": "device_list",
                        "timestamp": "now",
                        "data": device_list,
                    },
                    websocket,
                )
            else:
                logger.warning(f"Unknown WebSocket message: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/stats")
async def websocket_stats(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bandwidth statistics.

    Provides live updates of network statistics and top bandwidth consumers.
    Clients will receive automatic updates every 2 seconds with:
    - bandwidth_history: Last 20 data points
    - protocols: Protocol distribution percentages
    - current_bandwidth: Real-time bandwidth in Mbps
    - active_devices: Number of currently active devices
    - total_devices: Total unique devices seen
    """
    await manager.connect(websocket)

    try:
        # Send ping/pong to keep connection alive
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Stats WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket stats error: {e}")
        manager.disconnect(websocket)
