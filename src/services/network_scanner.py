"""Network scanner service for device discovery."""

import asyncio
import ipaddress
import socket
import subprocess
import platform
from typing import Any, Optional
from datetime import datetime

import psutil

from src.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_mac_address(mac: str) -> str:
    """
    Normalize MAC address to standard format (AA:BB:CC:DD:EE:FF).

    Args:
        mac: MAC address in various formats

    Returns:
        Normalized MAC address with uppercase letters and colons,
        with each octet padded to 2 digits
    """
    if not mac:
        return mac

    # Remove common separators and convert to uppercase
    cleaned = mac.upper().replace("-", ":").replace(".", ":")

    # Split by colons and pad each octet
    parts = cleaned.split(":")
    if len(parts) == 6:
        # Pad each octet to 2 digits
        octets = [part.zfill(2) for part in parts]
        return ":".join(octets)

    # Try removing all separators
    cleaned = cleaned.replace(":", "")
    if len(cleaned) == 12 and all(c in "0123456789ABCDEF" for c in cleaned):
        octets = [cleaned[i : i + 2] for i in range(0, 12, 2)]
        return ":".join(octets)

    # Return original if we can't parse it
    return mac


class NetworkScanner:
    """
    Network scanner for discovering devices on the local network.

    Uses multiple techniques:
    1. ARP table scanning (fastest, most reliable for local network)
    2. Active connections from psutil (currently active devices)
    3. Ping sweep (optional, more thorough but slower)
    4. Port scanning (optional, for detailed service discovery)
    """

    def __init__(self):
        self.discovered_devices: dict[str, dict[str, Any]] = {}
        self.last_scan_time: Optional[datetime] = None

    def get_local_network_ranges(self) -> list[str]:
        """
        Get local network IP ranges based on system interfaces.

        Returns:
            List of network ranges in CIDR notation (e.g., ['192.168.1.0/24'])
        """
        networks = []
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        ip = addr.address
                        netmask = addr.netmask

                        # Skip loopback
                        if ip.startswith("127."):
                            continue

                        # Calculate network address
                        try:
                            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                            networks.append(str(network))
                            logger.info(
                                f"Detected local network: {network} on interface {interface}"
                            )
                        except Exception as e:
                            logger.warning(f"Could not parse network for {ip}/{netmask}: {e}")
        except Exception as e:
            logger.error(f"Error getting local network ranges: {e}")

        return networks

    def scan_arp_table(self) -> dict[str, dict[str, Any]]:
        """
        Scan the system's ARP table for known devices.
        This is the fastest method as it uses cached data.

        Returns:
            Dictionary of IP addresses to device info
        """
        devices = {}
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)

                # Parse output: hostname (192.168.1.1) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
                for line in result.stdout.splitlines():
                    try:
                        parts = line.split()
                        if len(parts) >= 4 and "(" in parts[1] and ")" in parts[1]:
                            ip = parts[1].strip("()")
                            mac = parts[3] if parts[2] == "at" else None
                            hostname = parts[0] if parts[0] != "?" else None

                            if mac and mac != "(incomplete)":
                                devices[ip] = {
                                    "ip_address": ip,
                                    "mac_address": normalize_mac_address(mac),
                                    "hostname": hostname,
                                    "discovery_method": "arp",
                                    "last_seen": datetime.now(),
                                }
                    except Exception as e:
                        logger.debug(f"Could not parse ARP line: {line} - {e}")

            elif system == "Linux":
                result = subprocess.run(["arp", "-n"], capture_output=True, text=True, timeout=5)

                # Parse output: Address HWtype HWaddress Flags Mask Iface
                for line in result.stdout.splitlines()[1:]:  # Skip header
                    try:
                        parts = line.split()
                        if len(parts) >= 3:
                            ip = parts[0]
                            mac = parts[2]

                            if mac != "<incomplete>":
                                devices[ip] = {
                                    "ip_address": ip,
                                    "mac_address": normalize_mac_address(mac),
                                    "hostname": None,
                                    "discovery_method": "arp",
                                    "last_seen": datetime.now(),
                                }
                    except Exception as e:
                        logger.debug(f"Could not parse ARP line: {line} - {e}")

            elif system == "Windows":
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)

                # Parse Windows ARP output
                for line in result.stdout.splitlines():
                    try:
                        if "dynamic" in line.lower() or "static" in line.lower():
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[0]
                                mac = parts[1]

                                devices[ip] = {
                                    "ip_address": ip,
                                    "mac_address": normalize_mac_address(mac.replace("-", ":")),
                                    "hostname": None,
                                    "discovery_method": "arp",
                                    "last_seen": datetime.now(),
                                }
                    except Exception as e:
                        logger.debug(f"Could not parse ARP line: {line} - {e}")

            logger.info(f"Found {len(devices)} devices in ARP table")

        except subprocess.TimeoutExpired:
            logger.warning("ARP scan timed out")
        except Exception as e:
            logger.error(f"Error scanning ARP table: {e}")

        return devices

    def scan_active_connections(self) -> dict[str, dict[str, Any]]:
        """
        Scan currently active network connections using psutil.
        This finds devices that are currently communicating with this system.

        Returns:
            Dictionary of IP addresses to device info
        """
        devices = {}

        try:
            connections = psutil.net_connections(kind="inet")

            for conn in connections:
                # Only consider established connections
                if conn.status == "ESTABLISHED" and conn.raddr:
                    ip = conn.raddr.ip

                    # Skip loopback and multicast
                    if ip.startswith("127.") or ip.startswith("224."):
                        continue

                    if ip not in devices:
                        devices[ip] = {
                            "ip_address": ip,
                            "mac_address": None,  # Not available from connections
                            "hostname": None,
                            "discovery_method": "active_connection",
                            "last_seen": datetime.now(),
                            "remote_port": conn.raddr.port,
                            "local_port": conn.laddr.port if conn.laddr else None,
                        }

            logger.info(f"Found {len(devices)} devices from active connections")

        except Exception as e:
            logger.error(f"Error scanning active connections: {e}")

        return devices

    async def resolve_hostname(self, ip: str) -> str | None:
        """
        Resolve hostname for an IP address using multiple methods.

        Args:
            ip: IP address to resolve

        Returns:
            Hostname if found, None otherwise
        """
        # Try reverse DNS lookup first
        try:
            loop = asyncio.get_event_loop()
            hostname = await loop.run_in_executor(None, lambda: socket.gethostbyaddr(ip)[0])
            if hostname and hostname != ip:
                return hostname
        except Exception:
            pass

        # Try getfqdn as fallback
        try:
            loop = asyncio.get_event_loop()
            fqdn = await loop.run_in_executor(None, lambda: socket.getfqdn(ip))
            if fqdn and fqdn != ip and not fqdn.startswith(ip):
                return fqdn
        except Exception:
            pass

        # Try nslookup as last resort (works better in some network environments)
        try:
            result = await asyncio.create_subprocess_exec(
                "nslookup", ip, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=2)
            output = stdout.decode()

            # Parse nslookup output for name
            for line in output.splitlines():
                if "name =" in line.lower():
                    hostname = line.split("=")[1].strip().rstrip(".")
                    if hostname and hostname != ip:
                        return hostname
        except Exception:
            pass

        return None

    async def ping_host(self, ip: str, timeout: float = 1.0) -> bool:
        """
        Ping a host to check if it's alive.

        Args:
            ip: IP address to ping
            timeout: Timeout in seconds

        Returns:
            True if host responds, False otherwise
        """
        system = platform.system()

        try:
            if system == "Windows":
                cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )

            await asyncio.wait_for(result.wait(), timeout=timeout + 1)
            return result.returncode == 0

        except Exception:
            return False

    async def scan_network_range(
        self, network_range: str, use_ping: bool = False, max_concurrent: int = 50
    ) -> dict[str, dict[str, Any]]:
        """
        Scan a network range for active devices.

        Args:
            network_range: Network in CIDR notation (e.g., '192.168.1.0/24')
            use_ping: Whether to use ping sweep (slower but more thorough)
            max_concurrent: Maximum concurrent scans

        Returns:
            Dictionary of IP addresses to device info
        """
        devices = {}

        try:
            network = ipaddress.IPv4Network(network_range, strict=False)
            total_hosts = network.num_addresses - 2  # Exclude network and broadcast

            logger.info(f"Scanning network range {network_range} ({total_hosts} hosts)")

            if use_ping:
                # Ping sweep - scan all IPs in range
                semaphore = asyncio.Semaphore(max_concurrent)

                async def ping_with_semaphore(ip_str: str):
                    async with semaphore:
                        if await self.ping_host(ip_str):
                            hostname = await self.resolve_hostname(ip_str)
                            return ip_str, {
                                "ip_address": ip_str,
                                "mac_address": None,
                                "hostname": hostname,
                                "discovery_method": "ping_sweep",
                                "last_seen": datetime.now(),
                            }
                    return None, None

                # Create tasks for all IPs
                tasks = []
                for ip in network.hosts():
                    tasks.append(ping_with_semaphore(str(ip)))

                # Run with progress logging
                results = await asyncio.gather(*tasks)

                for ip, device_info in results:
                    if device_info:
                        devices[ip] = device_info

                logger.info(f"Ping sweep found {len(devices)} active devices")

        except Exception as e:
            logger.error(f"Error scanning network range {network_range}: {e}")

        return devices

    async def scan_all_networks(
        self, use_ping: bool = False, include_connections: bool = True
    ) -> dict[str, dict[str, Any]]:
        """
        Perform a comprehensive scan of all local networks.

        Args:
            use_ping: Whether to perform ping sweep (slower)
            include_connections: Whether to include active connections

        Returns:
            Dictionary of all discovered devices
        """
        all_devices = {}

        # 1. Quick scan - ARP table (always do this, it's fast)
        logger.info("Scanning ARP table...")
        arp_devices = self.scan_arp_table()
        all_devices.update(arp_devices)

        # 2. Active connections
        if include_connections:
            logger.info("Scanning active connections...")
            conn_devices = self.scan_active_connections()

            # Merge with ARP data (prefer ARP for MAC addresses)
            for ip, device in conn_devices.items():
                if ip in all_devices:
                    # Merge data, keeping existing MAC address
                    all_devices[ip].update(
                        {
                            k: v
                            for k, v in device.items()
                            if v is not None
                            and (k not in all_devices[ip] or all_devices[ip][k] is None)
                        }
                    )
                else:
                    all_devices[ip] = device

        # 3. Optional: Ping sweep for more thorough discovery
        if use_ping:
            logger.info("Performing ping sweep (this may take a while)...")
            network_ranges = self.get_local_network_ranges()

            for network_range in network_ranges:
                ping_devices = await self.scan_network_range(network_range, use_ping=True)

                # Merge with existing devices
                for ip, device in ping_devices.items():
                    if ip in all_devices:
                        all_devices[ip].update(
                            {
                                k: v
                                for k, v in device.items()
                                if v is not None
                                and (k not in all_devices[ip] or all_devices[ip][k] is None)
                            }
                        )
                    else:
                        all_devices[ip] = device

        # 4. After ping sweep, re-scan ARP table to get MAC addresses
        # (pinging devices often adds them to ARP cache)
        if use_ping:
            logger.info("Re-scanning ARP table for MAC addresses...")
            await asyncio.sleep(1)  # Brief delay for ARP cache to update
            arp_devices_post_ping = self.scan_arp_table()

            for ip, device in arp_devices_post_ping.items():
                if ip in all_devices and device.get("mac_address"):
                    all_devices[ip]["mac_address"] = device["mac_address"]
                elif ip not in all_devices:
                    all_devices[ip] = device

        # 5. Resolve hostnames for devices without them
        logger.info("Resolving hostnames...")
        for ip, device in all_devices.items():
            if not device.get("hostname"):
                hostname = await self.resolve_hostname(ip)
                if hostname:
                    device["hostname"] = hostname

        self.discovered_devices = all_devices
        self.last_scan_time = datetime.now()

        logger.info(f"Network scan complete. Found {len(all_devices)} total devices")
        return all_devices

    def get_device_vendor(self, mac_address: str) -> Optional[str]:
        """
        Get device vendor/manufacturer from MAC address OUI.

        Args:
            mac_address: MAC address in format aa:bb:cc:dd:ee:ff

        Returns:
            Vendor name if found, None otherwise
        """
        # This would require an OUI database lookup
        # For now, return None. Can be enhanced with a local OUI database
        # or API call to MAC vendor lookup service
        return None

    def classify_device_type(self, device_info: dict[str, Any]) -> str:
        """
        Attempt to classify device type based on available information.

        Args:
            device_info: Device information dictionary

        Returns:
            Device type classification
        """
        hostname = device_info.get("hostname", "").lower() if device_info.get("hostname") else ""

        # Simple heuristic-based classification
        if "iphone" in hostname or "ios" in hostname:
            return "mobile"
        elif "android" in hostname:
            return "mobile"
        elif "ipad" in hostname:
            return "tablet"
        elif "macbook" in hostname or "mac" in hostname:
            return "computer"
        elif "router" in hostname or "gateway" in hostname:
            return "router"
        elif "printer" in hostname:
            return "printer"
        elif "tv" in hostname or "roku" in hostname or "chromecast" in hostname:
            return "streaming"
        else:
            return "unknown"


# Global scanner instance
_network_scanner: Optional[NetworkScanner] = None


def get_network_scanner() -> NetworkScanner:
    """Get or create the global network scanner instance."""
    global _network_scanner
    if _network_scanner is None:
        _network_scanner = NetworkScanner()
    return _network_scanner
