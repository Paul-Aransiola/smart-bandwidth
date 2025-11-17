"""
Bandwidth control service using iptables and tc (traffic control).
Handles blocking and throttling of devices.
"""

import subprocess
from typing import Any

from src.core.config import get_settings
from src.core.exceptions import BandwidthControlException
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BandwidthController:
    """
    Bandwidth control service for blocking and throttling devices.
    Uses iptables for blocking and tc (traffic control) for throttling.
    """

    def __init__(self):
        """Initialize bandwidth controller."""
        self.logger = logger
        self.interface = settings.network_interface

    async def block_device(self, ip_address: str) -> bool:
        """
        Block a device by IP address using iptables.

        Args:
            ip_address: IP address to block

        Returns:
            True if successful

        Raises:
            BandwidthControlException: If blocking fails
        """
        if not settings.enable_blocking:
            self.logger.warning("Blocking is disabled in configuration")
            return False

        try:
            self.logger.info(f"Blocking device: {ip_address}")

            # Block incoming traffic from IP
            self._run_command(["iptables", "-A", "INPUT", "-s", ip_address, "-j", "DROP"])

            # Block outgoing traffic to IP
            self._run_command(["iptables", "-A", "OUTPUT", "-d", ip_address, "-j", "DROP"])

            self.logger.info(f"Successfully blocked device: {ip_address}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to block device {ip_address}: {e}")
            raise BandwidthControlException(f"Failed to block device: {e}") from e

    async def unblock_device(self, ip_address: str) -> bool:
        """
        Unblock a device by IP address.

        Args:
            ip_address: IP address to unblock

        Returns:
            True if successful

        Raises:
            BandwidthControlException: If unblocking fails
        """
        try:
            self.logger.info(f"Unblocking device: {ip_address}")

            # Remove incoming block rule
            self._run_command(["iptables", "-D", "INPUT", "-s", ip_address, "-j", "DROP"])

            # Remove outgoing block rule
            self._run_command(["iptables", "-D", "OUTPUT", "-d", ip_address, "-j", "DROP"])

            self.logger.info(f"Successfully unblocked device: {ip_address}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unblock device {ip_address}: {e}")
            raise BandwidthControlException(f"Failed to unblock device: {e}") from e

    async def throttle_device(self, ip_address: str, limit_mbps: float) -> bool:
        """
        Throttle a device's bandwidth using tc (traffic control).

        Args:
            ip_address: IP address to throttle
            limit_mbps: Bandwidth limit in Mbps

        Returns:
            True if successful

        Raises:
            BandwidthControlException: If throttling fails
        """
        if not settings.enable_throttling:
            self.logger.warning("Throttling is disabled in configuration")
            return False

        try:
            self.logger.info(f"Throttling device {ip_address} to {limit_mbps} Mbps")

            # Convert Mbps to kbps for tc
            limit_kbps = int(limit_mbps * 1024)

            # This is a simplified version. In production, you'd need more complex tc rules
            # Add qdisc and class for throttling
            self._run_command(
                [
                    "tc",
                    "qdisc",
                    "add",
                    "dev",
                    self.interface,
                    "root",
                    "handle",
                    "1:",
                    "htb",
                    "default",
                    "30",
                ]
            )

            self._run_command(
                [
                    "tc",
                    "class",
                    "add",
                    "dev",
                    self.interface,
                    "parent",
                    "1:",
                    "classid",
                    "1:1",
                    "htb",
                    "rate",
                    f"{limit_kbps}kbit",
                ]
            )

            # Add filter for IP
            self._run_command(
                [
                    "tc",
                    "filter",
                    "add",
                    "dev",
                    self.interface,
                    "protocol",
                    "ip",
                    "parent",
                    "1:0",
                    "prio",
                    "1",
                    "u32",
                    "match",
                    "ip",
                    "dst",
                    ip_address,
                    "flowid",
                    "1:1",
                ]
            )

            self.logger.info(f"Successfully throttled device: {ip_address}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to throttle device {ip_address}: {e}")
            raise BandwidthControlException(f"Failed to throttle device: {e}") from e

    async def unthrottle_device(self, ip_address: str) -> bool:
        """
        Remove bandwidth throttling from a device.

        Args:
            ip_address: IP address to unthrottle

        Returns:
            True if successful

        Raises:
            BandwidthControlException: If unthrottling fails
        """
        try:
            self.logger.info(f"Removing throttling from device: {ip_address}")

            # Remove tc rules (simplified - in production, track and remove specific rules)
            self._run_command(["tc", "qdisc", "del", "dev", self.interface, "root"])

            self.logger.info(f"Successfully removed throttling: {ip_address}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unthrottle device {ip_address}: {e}")
            raise BandwidthControlException(f"Failed to unthrottle device: {e}") from e

    def _run_command(self, command: list[str]) -> tuple[str, str]:
        """
        Run a system command with proper error handling.

        Args:
            command: Command and arguments as list

        Returns:
            Tuple of (stdout, stderr)

        Raises:
            BandwidthControlException: If command fails
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return result.stdout, result.stderr

        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {' '.join(command)}\nError: {e.stderr}"
            self.logger.error(error_msg)
            raise BandwidthControlException(error_msg) from e

        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out: {' '.join(command)}"
            self.logger.error(error_msg)
            raise BandwidthControlException(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error running command: {e}"
            self.logger.error(error_msg)
            raise BandwidthControlException(error_msg) from e

    def is_available(self) -> bool:
        """
        Check if required tools (iptables, tc) are available.

        Returns:
            True if tools are available
        """
        try:
            self._run_command(["which", "iptables"])
            self._run_command(["which", "tc"])
            return True
        except Exception:
            return False

    def get_status(self) -> dict[str, Any]:
        """
        Get controller status.

        Returns:
            Dictionary with controller status
        """
        return {
            "tools_available": self.is_available(),
            "blocking_enabled": settings.enable_blocking,
            "throttling_enabled": settings.enable_throttling,
            "interface": self.interface,
        }
