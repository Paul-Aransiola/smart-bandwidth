"""
Network monitoring service using Scapy and psutil.
Captures packets and tracks bandwidth per device.
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

import psutil
from scapy.all import AsyncSniffer, IP, sniff
from scapy.packet import Packet

from src.core.config import get_settings
from src.core.exceptions import NetworkMonitorException
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class NetworkMonitor:
    """
    Network monitoring service using Scapy for packet capture.
    Tracks bandwidth usage per IP/MAC address.
    """

    def __init__(self, interface: str | None = None):
        """
        Initialize network monitor.

        Args:
            interface: Network interface to monitor (e.g., 'eth0', 'wlan0')
        """
        self.interface = interface or settings.network_interface
        self.sniffer: AsyncSniffer | None = None
        self.is_running = False
        self.packet_count: dict[str, int] = defaultdict(int)
        self.byte_count: dict[str, dict[str, int]] = defaultdict(
            lambda: {"sent": 0, "received": 0}
        )
        self.logger = logger

    async def start(self) -> None:
        """Start network monitoring."""
        if self.is_running:
            self.logger.warning("Network monitor is already running")
            return

        try:
            self.logger.info(f"Starting network monitor on interface {self.interface}")
            self.is_running = True

            # Validate interface exists
            if not self._validate_interface():
                raise NetworkMonitorException(
                    f"Network interface '{self.interface}' not found or not available"
                )

            # Start packet capture in background
            asyncio.create_task(self._capture_packets())

            self.logger.info("Network monitor started successfully")

        except Exception as e:
            self.is_running = False
            self.logger.error(f"Failed to start network monitor: {e}")
            raise NetworkMonitorException(f"Failed to start monitoring: {e}")

    async def stop(self) -> None:
        """Stop network monitoring."""
        if not self.is_running:
            return

        self.logger.info("Stopping network monitor")
        self.is_running = False

        if self.sniffer:
            try:
                self.sniffer.stop()
            except Exception as e:
                self.logger.error(f"Error stopping sniffer: {e}")

        self.logger.info("Network monitor stopped")

    async def _capture_packets(self) -> None:
        """Capture packets using Scapy."""
        try:
            # Use AsyncSniffer for non-blocking capture
            self.sniffer = AsyncSniffer(
                iface=self.interface,
                prn=self._process_packet,
                store=False,
                filter=settings.capture_filter if settings.capture_filter else None,
            )

            self.sniffer.start()

            # Keep running while monitor is active
            while self.is_running:
                await asyncio.sleep(1)

        except PermissionError:
            self.logger.error("Permission denied: packet capture requires root/admin privileges")
            raise NetworkMonitorException(
                "Packet capture requires root/admin privileges. Run with sudo."
            )
        except Exception as e:
            self.logger.error(f"Packet capture error: {e}")
            raise NetworkMonitorException(f"Packet capture failed: {e}")

    def _process_packet(self, packet: Packet) -> None:
        """
        Process captured packet.

        Args:
            packet: Scapy packet object
        """
        try:
            # Check if packet has IP layer
            if IP not in packet:
                return

            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            packet_size = len(packet)

            # Track outgoing traffic (sent)
            self.byte_count[src_ip]["sent"] += packet_size
            self.packet_count[src_ip] += 1

            # Track incoming traffic (received)
            self.byte_count[dst_ip]["received"] += packet_size
            self.packet_count[dst_ip] += 1

        except Exception as e:
            self.logger.debug(f"Error processing packet: {e}")

    def _validate_interface(self) -> bool:
        """
        Validate that the network interface exists and is available.

        Returns:
            True if interface is valid, False otherwise
        """
        try:
            interfaces = psutil.net_if_addrs()
            return self.interface in interfaces
        except Exception as e:
            self.logger.error(f"Error validating interface: {e}")
            return False

    def get_device_stats(self, ip_address: str) -> dict[str, Any]:
        """
        Get bandwidth statistics for a specific IP address.

        Args:
            ip_address: IP address to get stats for

        Returns:
            Dictionary with bandwidth statistics
        """
        return {
            "ip_address": ip_address,
            "bytes_sent": self.byte_count[ip_address]["sent"],
            "bytes_received": self.byte_count[ip_address]["received"],
            "packet_count": self.packet_count[ip_address],
            "total_bytes": (
                self.byte_count[ip_address]["sent"]
                + self.byte_count[ip_address]["received"]
            ),
        }

    def get_all_stats(self) -> list[dict[str, Any]]:
        """
        Get bandwidth statistics for all monitored devices.

        Returns:
            List of device statistics
        """
        return [
            self.get_device_stats(ip)
            for ip in self.byte_count.keys()
        ]

    def reset_stats(self, ip_address: str | None = None) -> None:
        """
        Reset statistics for a device or all devices.

        Args:
            ip_address: IP address to reset, or None to reset all
        """
        if ip_address:
            self.byte_count[ip_address] = {"sent": 0, "received": 0}
            self.packet_count[ip_address] = 0
        else:
            self.byte_count.clear()
            self.packet_count.clear()

    def get_network_interfaces(self) -> list[str]:
        """
        Get list of available network interfaces.

        Returns:
            List of interface names
        """
        try:
            return list(psutil.net_if_addrs().keys())
        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
            return []

    def get_interface_stats(self) -> dict[str, Any]:
        """
        Get statistics for the monitored interface.

        Returns:
            Dictionary with interface statistics
        """
        try:
            stats = psutil.net_if_stats().get(self.interface)
            if not stats:
                return {}

            return {
                "interface": self.interface,
                "is_up": stats.isup,
                "speed": stats.speed,
                "mtu": stats.mtu,
            }
        except Exception as e:
            self.logger.error(f"Error getting interface stats: {e}")
            return {}


class BandwidthCalculator:
    """Helper class for calculating bandwidth speeds from byte counts."""

    @staticmethod
    def bytes_to_mbps(bytes_count: int, time_interval_seconds: float) -> float:
        """
        Convert bytes to Mbps.

        Args:
            bytes_count: Number of bytes transferred
            time_interval_seconds: Time interval in seconds

        Returns:
            Speed in Mbps
        """
        if time_interval_seconds <= 0:
            return 0.0

        # Convert bytes to megabits
        megabits = (bytes_count * 8) / (1024 * 1024)
        # Calculate speed
        return megabits / time_interval_seconds

    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        """
        Format bytes to human-readable string.

        Args:
            bytes_count: Number of bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} PB"
