"""
Unit tests for BandwidthController.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import BandwidthControlException
from src.services.bandwidth_controller import BandwidthController


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("src.services.bandwidth_controller.settings") as mock:
        mock.network_interface = "eth0"
        mock.enable_blocking = True
        mock.enable_throttling = True
        yield mock


@pytest.fixture
def controller(mock_settings):
    """Create bandwidth controller instance."""
    return BandwidthController()


@pytest.mark.asyncio
class TestBlockDevice:
    """Tests for device blocking."""

    async def test_block_device_success(self, controller):
        """Test successful device blocking."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("", "")

            result = await controller.block_device("192.168.1.100")

            assert result is True
            assert mock_run.call_count == 2
            # Verify INPUT rule
            mock_run.assert_any_call(
                ["iptables", "-A", "INPUT", "-s", "192.168.1.100", "-j", "DROP"]
            )
            # Verify OUTPUT rule
            mock_run.assert_any_call(
                ["iptables", "-A", "OUTPUT", "-d", "192.168.1.100", "-j", "DROP"]
            )

    async def test_block_device_when_disabled(self, controller, mock_settings):
        """Test blocking when disabled in settings."""
        mock_settings.enable_blocking = False

        result = await controller.block_device("192.168.1.100")

        assert result is False

    async def test_block_device_command_failure(self, controller):
        """Test blocking with command failure."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.side_effect = BandwidthControlException("iptables failed")

            with pytest.raises(BandwidthControlException, match="Failed to block device"):
                await controller.block_device("192.168.1.100")

    async def test_block_device_logs_actions(self, controller):
        """Test that blocking logs appropriate messages."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("", "")

            await controller.block_device("192.168.1.100")

            # Logger should be called (we're verifying the method completes)
            assert mock_run.called


@pytest.mark.asyncio
class TestUnblockDevice:
    """Tests for device unblocking."""

    async def test_unblock_device_success(self, controller):
        """Test successful device unblocking."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("", "")

            result = await controller.unblock_device("192.168.1.100")

            assert result is True
            assert mock_run.call_count == 2
            # Verify INPUT rule removal
            mock_run.assert_any_call(
                ["iptables", "-D", "INPUT", "-s", "192.168.1.100", "-j", "DROP"]
            )
            # Verify OUTPUT rule removal
            mock_run.assert_any_call(
                ["iptables", "-D", "OUTPUT", "-d", "192.168.1.100", "-j", "DROP"]
            )

    async def test_unblock_device_command_failure(self, controller):
        """Test unblocking with command failure."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.side_effect = BandwidthControlException("iptables failed")

            with pytest.raises(BandwidthControlException, match="Failed to unblock device"):
                await controller.unblock_device("192.168.1.100")


@pytest.mark.asyncio
class TestThrottleDevice:
    """Tests for device throttling."""

    async def test_throttle_device_success(self, controller):
        """Test successful device throttling."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("", "")

            result = await controller.throttle_device("192.168.1.100", 10.0)

            assert result is True
            # Should call tc commands for qdisc, class, and filter
            assert mock_run.call_count == 3

    async def test_throttle_device_when_disabled(self, controller, mock_settings):
        """Test throttling when disabled in settings."""
        mock_settings.enable_throttling = False

        result = await controller.throttle_device("192.168.1.100", 10.0)

        assert result is False

    async def test_throttle_device_converts_mbps_to_kbps(self, controller):
        """Test that Mbps is correctly converted to kbps."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("", "")

            await controller.throttle_device("192.168.1.100", 5.0)

            # 5 Mbps = 5120 kbps
            # Find the class add command
            calls = mock_run.call_args_list
            class_call = [c for c in calls if "class" in c[0][0] and "add" in c[0][0]][0]
            assert "5120kbit" in class_call[0][0]

    async def test_throttle_device_command_failure(self, controller):
        """Test throttling with command failure."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.side_effect = BandwidthControlException("tc failed")

            with pytest.raises(BandwidthControlException, match="Failed to throttle device"):
                await controller.throttle_device("192.168.1.100", 10.0)


@pytest.mark.asyncio
class TestUnthrottleDevice:
    """Tests for device unthrottling."""

    async def test_unthrottle_device_success(self, controller):
        """Test successful device unthrottling."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("", "")

            result = await controller.unthrottle_device("192.168.1.100")

            assert result is True
            # Should delete tc qdisc
            mock_run.assert_called_once_with(["tc", "qdisc", "del", "dev", "eth0", "root"])

    async def test_unthrottle_device_command_failure(self, controller):
        """Test unthrottling with command failure."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.side_effect = BandwidthControlException("tc failed")

            with pytest.raises(BandwidthControlException, match="Failed to unthrottle device"):
                await controller.unthrottle_device("192.168.1.100")


class TestRunCommand:
    """Tests for _run_command method."""

    def test_run_command_success(self, controller):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.stdout = "success"
        mock_result.stderr = ""

        with patch("src.services.bandwidth_controller.subprocess.run") as mock_run:
            mock_run.return_value = mock_result

            stdout, stderr = controller._run_command(["echo", "test"])

            assert stdout == "success"
            assert stderr == ""
            mock_run.assert_called_once()

    def test_run_command_with_error(self, controller):
        """Test command execution with CalledProcessError."""
        error = subprocess.CalledProcessError(1, ["test"], stderr="error output")

        with patch("src.services.bandwidth_controller.subprocess.run") as mock_run:
            mock_run.side_effect = error

            with pytest.raises(BandwidthControlException, match="Command failed"):
                controller._run_command(["test"])

    def test_run_command_timeout(self, controller):
        """Test command execution with timeout."""
        with patch("src.services.bandwidth_controller.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(["test"], 10)

            with pytest.raises(BandwidthControlException, match="Command timed out"):
                controller._run_command(["test"])

    def test_run_command_unexpected_error(self, controller):
        """Test command execution with unexpected error."""
        with patch("src.services.bandwidth_controller.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(BandwidthControlException, match="Unexpected error"):
                controller._run_command(["test"])

    def test_run_command_parameters(self, controller):
        """Test that command is called with correct parameters."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("src.services.bandwidth_controller.subprocess.run") as mock_run:
            mock_run.return_value = mock_result

            controller._run_command(["test", "command"])

            mock_run.assert_called_once_with(
                ["test", "command"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )


class TestIsAvailable:
    """Tests for is_available method."""

    def test_is_available_when_tools_exist(self, controller):
        """Test availability check when tools are available."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.return_value = ("/usr/bin/iptables", "")

            result = controller.is_available()

            assert result is True
            assert mock_run.call_count == 2
            mock_run.assert_any_call(["which", "iptables"])
            mock_run.assert_any_call(["which", "tc"])

    def test_is_available_when_tools_missing(self, controller):
        """Test availability check when tools are missing."""
        with patch.object(controller, "_run_command") as mock_run:
            mock_run.side_effect = BandwidthControlException("Command not found")

            result = controller.is_available()

            assert result is False


class TestGetStatus:
    """Tests for get_status method."""

    def test_get_status_all_enabled(self, controller):
        """Test status retrieval with all features enabled."""
        with patch.object(controller, "is_available", return_value=True):
            status = controller.get_status()

            assert status["tools_available"] is True
            assert status["blocking_enabled"] is True
            assert status["throttling_enabled"] is True
            assert status["interface"] == "eth0"

    def test_get_status_tools_unavailable(self, controller):
        """Test status retrieval when tools are unavailable."""
        with patch.object(controller, "is_available", return_value=False):
            status = controller.get_status()

            assert status["tools_available"] is False

    def test_get_status_features_disabled(self, controller, mock_settings):
        """Test status retrieval with features disabled."""
        mock_settings.enable_blocking = False
        mock_settings.enable_throttling = False

        with patch.object(controller, "is_available", return_value=True):
            status = controller.get_status()

            assert status["blocking_enabled"] is False
            assert status["throttling_enabled"] is False


class TestControllerInitialization:
    """Tests for controller initialization."""

    def test_initialization_with_default_settings(self, mock_settings):
        """Test controller initialization with default settings."""
        controller = BandwidthController()

        assert controller.interface == "eth0"
        assert controller.logger is not None

    def test_initialization_with_custom_interface(self, mock_settings):
        """Test controller initialization with custom interface."""
        mock_settings.network_interface = "wlan0"

        controller = BandwidthController()

        assert controller.interface == "wlan0"
