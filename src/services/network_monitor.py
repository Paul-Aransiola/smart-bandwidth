"""
Network monitoring service using Scapy and psutil.
Captures packets and tracks bandwidth per device.
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

import psutil
from scapy.all import AsyncSniffer, DNS, DNSQR, ICMP, IP, TCP, UDP, sniff
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
        self.byte_count: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "received": 0})

        # Protocol tracking
        self.protocol_count: dict[str, dict[str, int]] = defaultdict(
            lambda: {"tcp": 0, "udp": 0, "icmp": 0, "other": 0}
        )

        # Application tracking
        self.application_count: dict[str, dict[str, int]] = defaultdict(
            lambda: {"http": 0, "https": 0, "ssh": 0, "dns": 0, "ftp": 0, "other": 0}
        )

        # DNS query tracking
        self.dns_queries: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Connection tracking
        self.active_connections: dict[str, set[str]] = defaultdict(set)

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
        Process captured packet with enhanced protocol and application detection.

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

            # Protocol detection
            protocol = self._detect_protocol(packet)
            self.protocol_count[src_ip][protocol] += 1

            # Application detection
            application = self._detect_application(packet)
            self.application_count[src_ip][application] += 1

            # Track connections
            if protocol in ["tcp", "udp"]:
                connection_key = self._get_connection_key(packet, protocol)
                if connection_key:
                    self.active_connections[src_ip].add(connection_key)

            # DNS query tracking
            if DNS in packet and packet[DNS].qr == 0:  # DNS query (not response)
                self._track_dns_query(packet, src_ip)

        except Exception as e:
            self.logger.debug(f"Error processing packet: {e}")

    def _detect_protocol(self, packet: Packet) -> str:
        """
        Detect network protocol from packet.

        Args:
            packet: Scapy packet object

        Returns:
            Protocol name (tcp, udp, icmp, other)
        """
        if TCP in packet:
            return "tcp"
        elif UDP in packet:
            return "udp"
        elif ICMP in packet:
            return "icmp"
        return "other"

    def _detect_application(self, packet: Packet) -> str:
        """
        Detect application protocol based on port numbers.

        Args:
            packet: Scapy packet object

        Returns:
            Application name (http, https, ssh, dns, ftp, other)
        """
        try:
            if TCP in packet:
                port = packet[TCP].dport

                # Common application ports
                if port == 80:
                    return "http"
                elif port == 443:
                    return "https"
                elif port == 22:
                    return "ssh"
                elif port == 21 or port == 20:
                    return "ftp"
                elif port == 25 or port == 587 or port == 465:
                    return "smtp"
                elif port == 3306:
                    return "mysql"
                elif port == 5432:
                    return "postgresql"
                elif port in [8080, 8000, 3000, 5000]:
                    return "http"

            elif UDP in packet:
                port = packet[UDP].dport

                if port == 53:
                    return "dns"
                elif port == 123:
                    return "ntp"
                elif port == 67 or port == 68:
                    return "dhcp"

            return "other"

        except Exception:
            return "other"

    def _get_connection_key(self, packet: Packet, protocol: str) -> str | None:
        """
        Generate unique connection key for tracking.

        Args:
            packet: Scapy packet object
            protocol: Protocol type (tcp/udp)

        Returns:
            Connection key string or None
        """
        try:
            if protocol == "tcp" and TCP in packet:
                src_port = packet[TCP].sport
                dst_ip = packet[IP].dst
                dst_port = packet[TCP].dport
                return f"tcp:{dst_ip}:{dst_port}"

            elif protocol == "udp" and UDP in packet:
                src_port = packet[UDP].sport
                dst_ip = packet[IP].dst
                dst_port = packet[UDP].dport
                return f"udp:{dst_ip}:{dst_port}"

            return None

        except Exception:
            return None

    def _track_dns_query(self, packet: Packet, src_ip: str) -> None:
        """
        Track DNS queries for domain monitoring.

        Args:
            packet: Scapy packet object
            src_ip: Source IP address
        """
        try:
            if DNSQR in packet:
                query_name = packet[DNSQR].qname.decode("utf-8").rstrip(".")

                # Add to DNS query history (keep last 100 queries per IP)
                self.dns_queries[src_ip].append(
                    {
                        "domain": query_name,
                        "timestamp": datetime.now(),
                    }
                )

                # Limit history size
                if len(self.dns_queries[src_ip]) > 100:
                    self.dns_queries[src_ip] = self.dns_queries[src_ip][-100:]

        except Exception as e:
            self.logger.debug(f"Error tracking DNS query: {e}")

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

    def get_device_stats(self, ip_address: str, include_details: bool = False) -> dict[str, Any]:
        """
        Get bandwidth statistics for a specific IP address.

        Args:
            ip_address: IP address to get stats for
            include_details: Include protocol, application, and connection details

        Returns:
            Dictionary with bandwidth statistics
        """
        stats = {
            "ip_address": ip_address,
            "bytes_sent": self.byte_count[ip_address]["sent"],
            "bytes_received": self.byte_count[ip_address]["received"],
            "packet_count": self.packet_count[ip_address],
            "total_bytes": (
                self.byte_count[ip_address]["sent"] + self.byte_count[ip_address]["received"]
            ),
        }

        if include_details:
            stats.update(
                {
                    "protocols": dict(self.protocol_count[ip_address]),
                    "applications": dict(self.application_count[ip_address]),
                    "active_connections": len(self.active_connections[ip_address]),
                    "dns_queries_count": len(self.dns_queries[ip_address]),
                }
            )

        return stats

    def get_all_stats(self) -> list[dict[str, Any]]:
        """
        Get bandwidth statistics for all monitored devices.

        Returns:
            List of device statistics
        """
        return [self.get_device_stats(ip) for ip in self.byte_count.keys()]

    def reset_stats(self, ip_address: str | None = None) -> None:
        """
        Reset statistics for a device or all devices.

        Args:
            ip_address: IP address to reset, or None to reset all
        """
        if ip_address:
            self.byte_count[ip_address] = {"sent": 0, "received": 0}
            self.packet_count[ip_address] = 0
            self.protocol_count[ip_address] = {"tcp": 0, "udp": 0, "icmp": 0, "other": 0}
            self.application_count[ip_address] = {
                "http": 0,
                "https": 0,
                "ssh": 0,
                "dns": 0,
                "ftp": 0,
                "other": 0,
            }
            self.active_connections[ip_address].clear()
            self.dns_queries[ip_address].clear()
        else:
            self.byte_count.clear()
            self.packet_count.clear()
            self.protocol_count.clear()
            self.application_count.clear()
            self.active_connections.clear()
            self.dns_queries.clear()

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

    def get_protocol_stats(self, ip_address: str | None = None) -> dict[str, Any]:
        """
        Get protocol statistics for a device or all devices.

        Args:
            ip_address: IP address to get stats for, or None for all devices

        Returns:
            Dictionary with protocol statistics
        """
        if ip_address:
            return {
                "ip_address": ip_address,
                "protocols": dict(self.protocol_count[ip_address]),
            }

        # Aggregate statistics for all devices
        total_protocols = {"tcp": 0, "udp": 0, "icmp": 0, "other": 0}
        for protocols in self.protocol_count.values():
            for protocol, count in protocols.items():
                total_protocols[protocol] += count

        return {"total": total_protocols}

    def get_application_stats(self, ip_address: str | None = None) -> dict[str, Any]:
        """
        Get application statistics for a device or all devices.

        Args:
            ip_address: IP address to get stats for, or None for all devices

        Returns:
            Dictionary with application statistics
        """
        if ip_address:
            return {
                "ip_address": ip_address,
                "applications": dict(self.application_count[ip_address]),
            }

        # Aggregate statistics for all devices
        total_apps = {"http": 0, "https": 0, "ssh": 0, "dns": 0, "ftp": 0, "other": 0}
        for apps in self.application_count.values():
            for app, count in apps.items():
                total_apps[app] += count

        return {"total": total_apps}

    def get_dns_queries(self, ip_address: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get recent DNS queries for a specific IP address.

        Args:
            ip_address: IP address to get queries for
            limit: Maximum number of queries to return

        Returns:
            List of recent DNS queries
        """
        queries = self.dns_queries[ip_address]
        return queries[-limit:] if len(queries) > limit else queries

    def get_active_connections(self, ip_address: str) -> list[str]:
        """
        Get active connections for a specific IP address.

        Args:
            ip_address: IP address to get connections for

        Returns:
            List of active connection keys
        """
        return list(self.active_connections[ip_address])

    def get_top_talkers(self, limit: int = 10, metric: str = "total_bytes") -> list[dict[str, Any]]:
        """
        Get top devices by bandwidth usage.

        Args:
            limit: Maximum number of devices to return
            metric: Metric to sort by (total_bytes, bytes_sent, bytes_received, packet_count)

        Returns:
            List of top devices sorted by metric
        """
        all_stats = self.get_all_stats()

        # Sort by specified metric
        sorted_stats = sorted(all_stats, key=lambda x: x.get(metric, 0), reverse=True)

        return sorted_stats[:limit]


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
