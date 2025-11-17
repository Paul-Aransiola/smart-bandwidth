"""
WebSocket connection manager for real-time monitoring.

Handles WebSocket connections and broadcasts real-time updates to connected clients.
"""

import asyncio
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.device_repository import DeviceRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: list[WebSocket] = []
        self._broadcast_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
            )

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """
        Send a message to a specific client.

        Args:
            message: The message to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        async with self._broadcast_lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast_device_update(
        self, device_data: dict[str, Any], event_type: str = "device_update"
    ) -> None:
        """
        Broadcast a device update to all connected clients.

        Args:
            device_data: The device data to broadcast
            event_type: The type of event (device_update, device_blocked, etc.)
        """
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": device_data,
        }
        await self.broadcast(message)

    async def broadcast_bandwidth_stats(self, stats: dict[str, Any]) -> None:
        """
        Broadcast bandwidth statistics to all connected clients.

        Args:
            stats: The statistics to broadcast
        """
        message = {
            "type": "bandwidth_stats",
            "timestamp": datetime.now().isoformat(),
            "data": stats,
        }
        await self.broadcast(message)

    async def broadcast_device_list(self, db: AsyncSession) -> None:
        """
        Broadcast the current device list to all connected clients.

        Args:
            db: Database session
        """
        device_repo = DeviceRepository(db)
        devices = await device_repo.get_all(skip=0, limit=100)

        device_list = [
            {
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "hostname": device.hostname,
                "device_name": device.device_name,
                "status": device.status.value,
                "is_blocked": device.is_blocked,
                "is_throttled": device.is_throttled,
                "throttle_limit_mbps": device.throttle_limit_mbps,
                "total_bytes_sent": device.total_bytes_sent,
                "total_bytes_received": device.total_bytes_received,
            }
            for device in devices
        ]

        message = {
            "type": "device_list",
            "timestamp": datetime.now().isoformat(),
            "data": device_list,
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)


# Global instance
manager = ConnectionManager()
