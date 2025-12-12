"""Real-time statistics collection and management service."""

import asyncio
from collections import deque, defaultdict
from datetime import datetime
from typing import Any, Deque
import psutil

from src.utils.logger import get_logger
from src.services.websocket_manager import manager as websocket_manager

logger = get_logger(__name__)


class RealtimeStatsService:
    """Service for collecting and managing real-time network statistics."""

    def __init__(self, max_history: int = 60):
        """
        Initialize real-time stats service.

        Args:
            max_history: Maximum number of historical data points to keep (default: 60 for 1 minute)
        """
        self.max_history = max_history
        self.bandwidth_history: Deque[dict[str, Any]] = deque(maxlen=max_history)
        self.device_count_history: Deque[dict[str, Any]] = deque(maxlen=max_history)
        self.protocol_stats: dict[str, int] = defaultdict(int)
        self.unique_devices: set[str] = set()
        self.total_bytes_transferred = 0
        self.is_running = False
        self._task: asyncio.Task | None = None
        self._last_net_io = None
        self._last_timestamp = None

        # Historical snapshots for trend calculation (store every 30 seconds)
        self.stats_snapshots: Deque[dict[str, Any]] = deque(maxlen=120)  # 1 hour of snapshots
        self._snapshot_counter = 0

    async def start(self) -> None:
        """Start collecting real-time statistics."""
        if self.is_running:
            logger.warning("Real-time stats service is already running")
            return

        logger.info("Starting real-time stats collection service")
        self.is_running = True
        self._task = asyncio.create_task(self._collect_stats_loop())

    async def stop(self) -> None:
        """Stop collecting real-time statistics."""
        if not self.is_running:
            return

        logger.info("Stopping real-time stats collection service")
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _collect_stats_loop(self) -> None:
        """Background loop to collect statistics every second."""
        try:
            while self.is_running:
                await self._collect_current_stats()
                await asyncio.sleep(1)  # Collect every second
        except asyncio.CancelledError:
            logger.info("Real-time stats collection cancelled")
        except Exception as e:
            logger.error(f"Error in stats collection loop: {e}", exc_info=True)
            self.is_running = False

    async def _collect_current_stats(self) -> None:
        """Collect current network statistics."""
        try:
            # Get current network I/O counters
            net_io = psutil.net_io_counters()
            current_time = datetime.now()

            # Calculate bandwidth (bytes per second)
            bandwidth_mbps = 0.0
            if self._last_net_io and self._last_timestamp:
                time_delta = (current_time - self._last_timestamp).total_seconds()
                if time_delta > 0:
                    bytes_sent_delta = net_io.bytes_sent - self._last_net_io.bytes_sent
                    bytes_recv_delta = net_io.bytes_recv - self._last_net_io.bytes_recv
                    total_bytes_delta = bytes_sent_delta + bytes_recv_delta
                    # Convert to Mbps
                    bandwidth_mbps = (total_bytes_delta * 8) / (time_delta * 1_000_000)
                    # Track total bytes
                    self.total_bytes_transferred += total_bytes_delta

            # Store bandwidth data point
            bandwidth_data = {
                "time": current_time.strftime("%H:%M:%S"),
                "timestamp": current_time.isoformat(),
                "bandwidth": round(bandwidth_mbps, 2),
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            }
            self.bandwidth_history.append(bandwidth_data)

            # Get active network connections and analyze protocols
            try:
                connections = psutil.net_connections(kind="inet")
                unique_ips = set()
                protocol_counts = defaultdict(int)

                for conn in connections:
                    if conn.raddr and conn.status == "ESTABLISHED":
                        unique_ips.add(conn.raddr.ip)

                        # Identify protocol based on port and type
                        if conn.type == 1:  # SOCK_STREAM = TCP
                            if conn.laddr.port == 80 or conn.raddr.port == 80:
                                protocol_counts["HTTP"] += 1
                            elif conn.laddr.port == 443 or conn.raddr.port == 443:
                                protocol_counts["HTTPS"] += 1
                            else:
                                protocol_counts["TCP"] += 1
                        elif conn.type == 2:  # SOCK_DGRAM = UDP
                            protocol_counts["UDP"] += 1
                        else:
                            protocol_counts["Other"] += 1

                # Update global protocol stats (cumulative)
                for protocol, count in protocol_counts.items():
                    self.protocol_stats[protocol] += count

                # Update unique devices set
                self.unique_devices.update(unique_ips)
                device_count = len(unique_ips)

            except (psutil.AccessDenied, PermissionError):
                # Fallback if we don't have permission
                device_count = 0

            device_data = {
                "time": current_time.strftime("%H:%M:%S"),
                "timestamp": current_time.isoformat(),
                "count": device_count,
            }
            self.device_count_history.append(device_data)

            # Take snapshots every 30 seconds for trend calculation
            self._snapshot_counter += 1
            if self._snapshot_counter >= 30:  # Every 30 seconds
                self._take_snapshot(current_time)
                self._snapshot_counter = 0

            # Broadcast to WebSocket clients every 2 seconds
            if self._snapshot_counter % 2 == 0:
                await self._broadcast_stats()

            # Update for next iteration
            self._last_net_io = net_io
            self._last_timestamp = current_time

        except Exception as e:
            logger.error(f"Error collecting current stats: {e}", exc_info=True)

    def _take_snapshot(self, timestamp: datetime) -> None:
        """Take a snapshot of current statistics for trend calculation."""
        snapshot = {
            "timestamp": timestamp.isoformat(),
            "total_devices": len(self.unique_devices),
            "active_devices": self.device_count_history[-1]["count"]
            if self.device_count_history
            else 0,
            "total_bandwidth": self.total_bytes_transferred,
            "current_bandwidth_mbps": self.bandwidth_history[-1]["bandwidth"]
            if self.bandwidth_history
            else 0,
        }
        self.stats_snapshots.append(snapshot)

    def _calculate_trend(self, current_value: float, field_name: str) -> dict[str, Any]:
        """Calculate percentage change trend for a field."""
        if len(self.stats_snapshots) < 2:
            return {"value": 0, "is_positive": True}

        # Compare with snapshot from 5 minutes ago (10 snapshots ago at 30s intervals)
        comparison_index = max(0, len(self.stats_snapshots) - 10)
        old_snapshot = self.stats_snapshots[comparison_index]
        old_value = old_snapshot.get(field_name, 0)

        if old_value == 0:
            return {"value": 0, "is_positive": True}

        percentage_change = ((current_value - old_value) / old_value) * 100

        return {"value": round(abs(percentage_change), 1), "is_positive": percentage_change >= 0}

    def get_bandwidth_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get bandwidth history.

        Args:
            limit: Maximum number of data points to return

        Returns:
            List of bandwidth data points
        """
        history = list(self.bandwidth_history)
        if limit and limit < len(history):
            # Return evenly distributed samples
            step = len(history) / limit
            indices = [int(i * step) for i in range(limit)]
            return [history[i] for i in indices if i < len(history)]
        return history

    def get_device_count_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get device count history.

        Args:
            limit: Maximum number of data points to return

        Returns:
            List of device count data points
        """
        history = list(self.device_count_history)
        if limit and limit < len(history):
            step = len(history) / limit
            indices = [int(i * step) for i in range(limit)]
            return [history[i] for i in indices if i < len(history)]
        return history

    def get_latest_stats(self) -> dict[str, Any]:
        """
        Get the latest collected statistics.

        Returns:
            Dictionary with latest bandwidth and device count
        """
        latest_bandwidth = self.bandwidth_history[-1] if self.bandwidth_history else None
        latest_devices = self.device_count_history[-1] if self.device_count_history else None

        return {
            "bandwidth": latest_bandwidth,
            "devices": latest_devices,
            "history_size": len(self.bandwidth_history),
            "is_collecting": self.is_running,
        }

    def get_protocol_stats(self) -> dict[str, int]:
        """
        Get protocol distribution statistics.

        Returns:
            Dictionary with protocol names and their connection counts
        """
        return dict(self.protocol_stats)

    def get_aggregated_stats(self) -> dict[str, Any]:
        """
        Get aggregated statistics including devices, bandwidth, and protocols.

        Returns:
            Dictionary with comprehensive statistics and trends
        """
        total_devices = len(self.unique_devices)
        active_devices = self.device_count_history[-1]["count"] if self.device_count_history else 0
        current_bandwidth = self.bandwidth_history[-1]["bandwidth"] if self.bandwidth_history else 0

        # Calculate average bandwidth per device
        avg_per_device = 0
        if total_devices > 0 and self.total_bytes_transferred > 0:
            avg_per_device = self.total_bytes_transferred / total_devices

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "total_bandwidth": self.total_bytes_transferred,
            "current_bandwidth_mbps": current_bandwidth,
            "average_bandwidth_per_device": avg_per_device,
            "protocol_distribution": self.get_protocol_stats(),
            "trends": {
                "total_devices": self._calculate_trend(total_devices, "total_devices"),
                "active_devices": self._calculate_trend(active_devices, "active_devices"),
                "total_bandwidth": self._calculate_trend(
                    self.total_bytes_transferred, "total_bandwidth"
                ),
                "average_bandwidth_per_device": self._calculate_trend(
                    avg_per_device, "total_bandwidth"
                ),
            },
        }

    def get_combined_history(
        self, limit: int = 20, active_device_count: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get combined bandwidth and device count history.

        Args:
            limit: Number of data points to return
            active_device_count: Override device count with actual database count

        Returns:
            List of combined data points
        """
        bandwidth_hist = self.get_bandwidth_history(limit)
        device_hist = self.get_device_count_history(limit)

        # Merge by timestamp
        combined = []
        for bw_point in bandwidth_hist:
            # Find matching device count by timestamp
            device_count = active_device_count if active_device_count is not None else 0
            if device_count == 0:
                for dev_point in device_hist:
                    if dev_point["time"] == bw_point["time"]:
                        device_count = dev_point["count"]
                        break

            combined.append(
                {
                    "time": bw_point["time"],
                    "bandwidth": bw_point["bandwidth"],
                    "devices": device_count,
                }
            )

        return combined

    async def _broadcast_stats(self) -> None:
        """Broadcast current stats to all WebSocket clients."""
        try:
            # Only broadcast if we have active connections
            if websocket_manager.get_connection_count() == 0:
                return

            # Get combined history for broadcast
            combined_history = self.get_combined_history(limit=20)
            protocol_stats = self.get_protocol_stats()

            # Get latest bandwidth and device count
            latest_bandwidth = (
                self.bandwidth_history[-1]["bandwidth"] if self.bandwidth_history else 0
            )
            latest_devices = (
                self.device_count_history[-1]["count"] if self.device_count_history else 0
            )

            # Calculate protocol distribution percentages
            total_connections = sum(protocol_stats.values())
            protocol_distribution = {}
            if total_connections > 0:
                for protocol, count in protocol_stats.items():
                    protocol_distribution[protocol] = round((count / total_connections) * 100, 1)

            message = {
                "bandwidth_history": combined_history,
                "protocols": protocol_distribution,
                "current_bandwidth": latest_bandwidth,
                "active_devices": latest_devices,
                "total_devices": len(self.unique_devices),
            }

            await websocket_manager.broadcast_bandwidth_stats(message)
        except Exception as e:
            # Don't let broadcast errors stop stats collection
            logger.debug(f"WebSocket broadcast error (non-critical): {e}")


# Global instance
_realtime_stats_service: RealtimeStatsService | None = None


def get_realtime_stats_service() -> RealtimeStatsService:
    """Get the global real-time stats service instance."""
    global _realtime_stats_service
    if _realtime_stats_service is None:
        _realtime_stats_service = RealtimeStatsService()
    return _realtime_stats_service


async def start_realtime_stats_service() -> None:
    """Start the global real-time stats service."""
    service = get_realtime_stats_service()
    await service.start()


async def stop_realtime_stats_service() -> None:
    """Stop the global real-time stats service."""
    service = get_realtime_stats_service()
    await service.stop()
