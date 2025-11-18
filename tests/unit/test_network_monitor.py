"""
Unit tests for NetworkMonitor and BandwidthCalculator.
"""

from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import NetworkMonitorException
from src.services.network_monitor import BandwidthCalculator, NetworkMonitor


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("src.services.network_monitor.settings") as mock:
        mock.network_interface = "eth0"
        mock.capture_filter = None
        yield mock


@pytest.fixture
def monitor(mock_settings):
    """Create network monitor instance."""
    return NetworkMonitor()


@pytest.mark.asyncio
class TestNetworkMonitorStartStop:
    """Tests for starting and stopping the monitor."""

    async def test_start_success(self, monitor):
        """Test successful monitor start."""
        with (
            patch.object(monitor, "_validate_interface", return_value=True),
            patch("asyncio.create_task") as mock_task,
        ):
            await monitor.start()

            assert monitor.is_running is True
            mock_task.assert_called_once()

    async def test_start_already_running(self, monitor):
        """Test starting monitor when already running."""
        monitor.is_running = True

        with (
            patch.object(monitor, "_validate_interface", return_value=True),
            patch("asyncio.create_task") as mock_task,
        ):
            await monitor.start()

            # Should not create new task
            mock_task.assert_not_called()

    async def test_start_invalid_interface(self, monitor):
        """Test starting monitor with invalid interface."""
        with patch.object(monitor, "_validate_interface", return_value=False):
            with pytest.raises(NetworkMonitorException, match="not found or not available"):
                await monitor.start()

            assert monitor.is_running is False

    async def test_start_exception(self, monitor):
        """Test start with unexpected exception."""
        with patch.object(monitor, "_validate_interface", side_effect=RuntimeError("Error")):
            with pytest.raises(NetworkMonitorException, match="Failed to start monitoring"):
                await monitor.start()

            assert monitor.is_running is False

    async def test_stop_when_running(self, monitor):
        """Test stopping monitor when running."""
        monitor.is_running = True
        monitor.sniffer = MagicMock()

        await monitor.stop()

        assert monitor.is_running is False
        monitor.sniffer.stop.assert_called_once()

    async def test_stop_when_not_running(self, monitor):
        """Test stopping monitor when not running."""
        monitor.is_running = False

        await monitor.stop()

        # Should complete without error
        assert monitor.is_running is False

    async def test_stop_with_sniffer_error(self, monitor):
        """Test stopping monitor with sniffer error."""
        monitor.is_running = True
        monitor.sniffer = MagicMock()
        monitor.sniffer.stop.side_effect = RuntimeError("Stop error")

        # Should not raise exception
        await monitor.stop()

        assert monitor.is_running is False


@pytest.mark.asyncio
class TestPacketCapture:
    """Tests for packet capture functionality."""

    async def test_capture_packets_starts_sniffer(self, monitor):
        """Test that packet capture starts AsyncSniffer."""
        mock_sniffer = MagicMock()
        mock_sniffer.start = MagicMock()

        with patch("src.services.network_monitor.AsyncSniffer", return_value=mock_sniffer):
            monitor.is_running = True

            # Start capture task
            task = monitor._capture_packets()

            # Stop immediately to prevent infinite loop
            monitor.is_running = False

            await task

            mock_sniffer.start.assert_called_once()

    async def test_capture_packets_permission_error(self, monitor):
        """Test packet capture with permission error."""
        with patch("src.services.network_monitor.AsyncSniffer") as mock_sniffer:
            mock_sniffer.return_value.start.side_effect = PermissionError("Permission denied")

            monitor.is_running = True

            with pytest.raises(NetworkMonitorException, match="requires root/admin privileges"):
                await monitor._capture_packets()

    async def test_capture_packets_generic_error(self, monitor):
        """Test packet capture with generic error."""
        with patch("src.services.network_monitor.AsyncSniffer") as mock_sniffer:
            mock_sniffer.return_value.start.side_effect = RuntimeError("Capture error")

            monitor.is_running = True

            with pytest.raises(NetworkMonitorException, match="Packet capture failed"):
                await monitor._capture_packets()


class TestProcessPacket:
    """Tests for packet processing."""

    def test_process_packet_with_ip(self, monitor):
        """Test processing packet with IP layer."""
        # Create mock packet with IP layer
        mock_packet = MagicMock()
        mock_packet.__len__.return_value = 1500

        # Mock IP layer
        mock_ip_layer = MagicMock()
        mock_ip_layer.src = "192.168.1.100"
        mock_ip_layer.dst = "192.168.1.200"

        # Configure packet to return IP layer
        def getitem(self, key):
            from src.services.network_monitor import IP

            if key == IP:
                return mock_ip_layer
            raise KeyError(key)

        mock_packet.__getitem__ = getitem

        # Configure IP membership test
        def contains(self, item):
            from src.services.network_monitor import IP

            return item == IP

        mock_packet.__contains__ = contains

        monitor._process_packet(mock_packet)

        # Verify byte counts were updated
        assert monitor.byte_count["192.168.1.100"]["sent"] == 1500
        assert monitor.byte_count["192.168.1.200"]["received"] == 1500
        assert monitor.packet_count["192.168.1.100"] == 1
        assert monitor.packet_count["192.168.1.200"] == 1

    def test_process_packet_without_ip(self, monitor):
        """Test processing packet without IP layer."""
        mock_packet = MagicMock()

        with patch("src.services.network_monitor.IP") as mock_ip:
            mock_ip.__contains__ = MagicMock(return_value=False)

            monitor._process_packet(mock_packet)

            # Should not update any counts
            assert len(monitor.byte_count) == 0
            assert len(monitor.packet_count) == 0

    def test_process_packet_with_error(self, monitor):
        """Test packet processing with error."""
        mock_packet = MagicMock()
        mock_packet.__len__ = MagicMock(side_effect=RuntimeError("Error"))

        with patch("src.services.network_monitor.IP") as mock_ip:
            mock_ip.__contains__ = MagicMock(return_value=True)

            # Should not raise exception
            monitor._process_packet(mock_packet)

    def test_process_packet_accumulates_bytes(self, monitor):
        """Test that multiple packets accumulate byte counts."""
        mock_packet = MagicMock()
        mock_packet.__len__.return_value = 1000

        # Mock IP layer
        mock_ip_layer = MagicMock()
        mock_ip_layer.src = "192.168.1.100"
        mock_ip_layer.dst = "192.168.1.200"

        # Configure packet to return IP layer
        def getitem(self, key):
            from src.services.network_monitor import IP

            if key == IP:
                return mock_ip_layer
            raise KeyError(key)

        mock_packet.__getitem__ = getitem

        # Configure IP membership test
        def contains(self, item):
            from src.services.network_monitor import IP

            return item == IP

        mock_packet.__contains__ = contains

        # Process 3 packets
        monitor._process_packet(mock_packet)
        monitor._process_packet(mock_packet)
        monitor._process_packet(mock_packet)

        assert monitor.byte_count["192.168.1.100"]["sent"] == 3000
        assert monitor.packet_count["192.168.1.100"] == 3


class TestValidateInterface:
    """Tests for interface validation."""

    def test_validate_interface_exists(self, monitor):
        """Test validation when interface exists."""
        with patch("src.services.network_monitor.psutil.net_if_addrs") as mock_addrs:
            mock_addrs.return_value = {"eth0": [], "wlan0": []}

            result = monitor._validate_interface()

            assert result is True

    def test_validate_interface_not_exists(self, monitor):
        """Test validation when interface doesn't exist."""
        with patch("src.services.network_monitor.psutil.net_if_addrs") as mock_addrs:
            mock_addrs.return_value = {"wlan0": []}

            result = monitor._validate_interface()

            assert result is False

    def test_validate_interface_error(self, monitor):
        """Test validation with psutil error."""
        with patch("src.services.network_monitor.psutil.net_if_addrs") as mock_addrs:
            mock_addrs.side_effect = RuntimeError("Error")

            result = monitor._validate_interface()

            assert result is False


class TestGetDeviceStats:
    """Tests for getting device statistics."""

    def test_get_device_stats_existing_device(self, monitor):
        """Test getting stats for device with data."""
        monitor.byte_count["192.168.1.100"] = {"sent": 1000, "received": 2000}
        monitor.packet_count["192.168.1.100"] = 50

        stats = monitor.get_device_stats("192.168.1.100")

        assert stats["ip_address"] == "192.168.1.100"
        assert stats["bytes_sent"] == 1000
        assert stats["bytes_received"] == 2000
        assert stats["packet_count"] == 50
        assert stats["total_bytes"] == 3000

    def test_get_device_stats_new_device(self, monitor):
        """Test getting stats for device with no data."""
        stats = monitor.get_device_stats("192.168.1.100")

        assert stats["ip_address"] == "192.168.1.100"
        assert stats["bytes_sent"] == 0
        assert stats["bytes_received"] == 0
        assert stats["packet_count"] == 0
        assert stats["total_bytes"] == 0


class TestGetAllStats:
    """Tests for getting all statistics."""

    def test_get_all_stats_with_devices(self, monitor):
        """Test getting all stats with multiple devices."""
        monitor.byte_count["192.168.1.100"] = {"sent": 1000, "received": 2000}
        monitor.byte_count["192.168.1.101"] = {"sent": 500, "received": 1500}
        monitor.packet_count["192.168.1.100"] = 50
        monitor.packet_count["192.168.1.101"] = 25

        stats = monitor.get_all_stats()

        assert len(stats) == 2
        assert any(s["ip_address"] == "192.168.1.100" for s in stats)
        assert any(s["ip_address"] == "192.168.1.101" for s in stats)

    def test_get_all_stats_empty(self, monitor):
        """Test getting all stats with no devices."""
        stats = monitor.get_all_stats()

        assert stats == []


class TestResetStats:
    """Tests for resetting statistics."""

    def test_reset_stats_single_device(self, monitor):
        """Test resetting stats for single device."""
        monitor.byte_count["192.168.1.100"] = {"sent": 1000, "received": 2000}
        monitor.byte_count["192.168.1.101"] = {"sent": 500, "received": 1500}
        monitor.packet_count["192.168.1.100"] = 50
        monitor.packet_count["192.168.1.101"] = 25

        monitor.reset_stats("192.168.1.100")

        assert monitor.byte_count["192.168.1.100"] == {"sent": 0, "received": 0}
        assert monitor.packet_count["192.168.1.100"] == 0
        # Other device should be unchanged
        assert monitor.byte_count["192.168.1.101"]["sent"] == 500

    def test_reset_stats_all_devices(self, monitor):
        """Test resetting stats for all devices."""
        monitor.byte_count["192.168.1.100"] = {"sent": 1000, "received": 2000}
        monitor.byte_count["192.168.1.101"] = {"sent": 500, "received": 1500}
        monitor.packet_count["192.168.1.100"] = 50
        monitor.packet_count["192.168.1.101"] = 25

        monitor.reset_stats()

        assert len(monitor.byte_count) == 0
        assert len(monitor.packet_count) == 0


class TestGetNetworkInterfaces:
    """Tests for getting network interfaces."""

    def test_get_network_interfaces_success(self, monitor):
        """Test getting network interfaces successfully."""
        with patch("src.services.network_monitor.psutil.net_if_addrs") as mock_addrs:
            mock_addrs.return_value = {"eth0": [], "wlan0": [], "lo": []}

            interfaces = monitor.get_network_interfaces()

            assert "eth0" in interfaces
            assert "wlan0" in interfaces
            assert "lo" in interfaces
            assert len(interfaces) == 3

    def test_get_network_interfaces_error(self, monitor):
        """Test getting network interfaces with error."""
        with patch("src.services.network_monitor.psutil.net_if_addrs") as mock_addrs:
            mock_addrs.side_effect = RuntimeError("Error")

            interfaces = monitor.get_network_interfaces()

            assert interfaces == []


class TestGetInterfaceStats:
    """Tests for getting interface statistics."""

    def test_get_interface_stats_success(self, monitor):
        """Test getting interface stats successfully."""
        mock_stats = MagicMock()
        mock_stats.isup = True
        mock_stats.speed = 1000
        mock_stats.mtu = 1500

        with patch("src.services.network_monitor.psutil.net_if_stats") as mock_if_stats:
            mock_if_stats.return_value = {"eth0": mock_stats}

            stats = monitor.get_interface_stats()

            assert stats["interface"] == "eth0"
            assert stats["is_up"] is True
            assert stats["speed"] == 1000
            assert stats["mtu"] == 1500

    def test_get_interface_stats_not_found(self, monitor):
        """Test getting stats for non-existent interface."""
        with patch("src.services.network_monitor.psutil.net_if_stats") as mock_if_stats:
            mock_if_stats.return_value = {}

            stats = monitor.get_interface_stats()

            assert stats == {}

    def test_get_interface_stats_error(self, monitor):
        """Test getting interface stats with error."""
        with patch("src.services.network_monitor.psutil.net_if_stats") as mock_if_stats:
            mock_if_stats.side_effect = RuntimeError("Error")

            stats = monitor.get_interface_stats()

            assert stats == {}


class TestNetworkMonitorInitialization:
    """Tests for monitor initialization."""

    def test_initialization_with_default_interface(self, mock_settings):
        """Test monitor initialization with default interface."""
        monitor = NetworkMonitor()

        assert monitor.interface == "eth0"
        assert monitor.is_running is False
        assert isinstance(monitor.packet_count, defaultdict)
        assert isinstance(monitor.byte_count, defaultdict)

    def test_initialization_with_custom_interface(self, mock_settings):
        """Test monitor initialization with custom interface."""
        monitor = NetworkMonitor(interface="wlan0")

        assert monitor.interface == "wlan0"

    def test_initialization_defaults(self, mock_settings):
        """Test monitor initialization defaults."""
        monitor = NetworkMonitor()

        assert monitor.sniffer is None
        assert len(monitor.packet_count) == 0
        assert len(monitor.byte_count) == 0


class TestBandwidthCalculator:
    """Tests for BandwidthCalculator."""

    def test_bytes_to_mbps_normal(self):
        """Test bytes to Mbps conversion."""
        # 1 MB in 1 second = 8 Mbps
        result = BandwidthCalculator.bytes_to_mbps(1024 * 1024, 1.0)

        assert result == 8.0

    def test_bytes_to_mbps_zero_time(self):
        """Test bytes to Mbps with zero time interval."""
        result = BandwidthCalculator.bytes_to_mbps(1024 * 1024, 0.0)

        assert result == 0.0

    def test_bytes_to_mbps_negative_time(self):
        """Test bytes to Mbps with negative time interval."""
        result = BandwidthCalculator.bytes_to_mbps(1024 * 1024, -1.0)

        assert result == 0.0

    def test_bytes_to_mbps_large_values(self):
        """Test bytes to Mbps with large values."""
        # 100 MB in 10 seconds = 80 Mbps
        result = BandwidthCalculator.bytes_to_mbps(100 * 1024 * 1024, 10.0)

        assert result == 80.0

    def test_format_bytes_small(self):
        """Test formatting small byte values."""
        result = BandwidthCalculator.format_bytes(500)

        assert result == "500.00 B"

    def test_format_bytes_kilobytes(self):
        """Test formatting kilobyte values."""
        result = BandwidthCalculator.format_bytes(2048)

        assert result == "2.00 KB"

    def test_format_bytes_megabytes(self):
        """Test formatting megabyte values."""
        result = BandwidthCalculator.format_bytes(5 * 1024 * 1024)

        assert result == "5.00 MB"

    def test_format_bytes_gigabytes(self):
        """Test formatting gigabyte values."""
        result = BandwidthCalculator.format_bytes(3 * 1024 * 1024 * 1024)

        assert result == "3.00 GB"

    def test_format_bytes_terabytes(self):
        """Test formatting terabyte values."""
        result = BandwidthCalculator.format_bytes(2 * 1024 * 1024 * 1024 * 1024)

        assert result == "2.00 TB"

    def test_format_bytes_zero(self):
        """Test formatting zero bytes."""
        result = BandwidthCalculator.format_bytes(0)

        assert result == "0.00 B"
