"""
Bandwidth threshold monitoring service.
Monitors device bandwidth usage and auto-deactivates devices exceeding thresholds.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.device import Device, DeviceStatus
from src.repositories.bandwidth_repository import BandwidthUsageRepository
from src.repositories.device_repository import DeviceRepository
from src.repositories.advanced_controls_repository import GlobalSettingsRepository
from src.repositories.user_repository import UserRepository
from src.services.bandwidth_controller import BandwidthController
from src.services.notification_handlers import NotificationManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BandwidthThresholdMonitor:
    """
    Service for monitoring bandwidth thresholds and auto-deactivating devices.
    """

    def __init__(
        self,
        check_interval_seconds: int = 60,
    ):
        """
        Initialize threshold monitor.

        Args:
            check_interval_seconds: How often to check thresholds (default: 60 seconds)
        """
        self.check_interval_seconds = check_interval_seconds
        self.is_running = False
        self._task: asyncio.Task | None = None
        self.notification_manager = NotificationManager()
        self.bandwidth_controller = BandwidthController()
        self.logger = logger

    async def start(self) -> None:
        """Start the threshold monitoring service."""
        if self.is_running:
            self.logger.warning("Threshold monitor is already running")
            return

        self.logger.info(
            f"Starting bandwidth threshold monitor (check interval: {self.check_interval_seconds}s)"
        )
        self.is_running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Threshold monitor started successfully")

    async def stop(self) -> None:
        """Stop the threshold monitoring service."""
        if not self.is_running:
            return

        self.logger.info("Stopping threshold monitor")
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Threshold monitor stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that checks thresholds periodically."""
        while self.is_running:
            try:
                await self._check_all_thresholds()
            except Exception as e:
                self.logger.error(f"Error in threshold monitoring loop: {e}", exc_info=True)

            # Wait for next check interval
            await asyncio.sleep(self.check_interval_seconds)

    async def _check_all_thresholds(self) -> dict[str, int]:
        """
        Check bandwidth thresholds for all devices with thresholds configured.

        Returns:
            Dictionary with counts: devices_checked, thresholds_breached, devices_deactivated
        """
        async for session in get_db():
            try:
                device_repo = DeviceRepository(session)
                bandwidth_repo = BandwidthUsageRepository(session)
                settings_repo = GlobalSettingsRepository(session)

                # Get global threshold settings
                global_threshold_str = await settings_repo.get_value(
                    "global_bandwidth_threshold_mbps"
                )
                global_threshold = float(global_threshold_str) if global_threshold_str else None
                global_auto_deactivate_str = await settings_repo.get_value(
                    "global_auto_deactivate_on_threshold"
                )
                global_auto_deactivate = (
                    global_auto_deactivate_str == "true" if global_auto_deactivate_str else False
                )
                global_time_window_str = await settings_repo.get_value(
                    "global_threshold_time_window_minutes"
                )
                global_time_window = int(global_time_window_str) if global_time_window_str else 5

                # Get devices with individual thresholds
                devices_with_thresholds = await device_repo.get_devices_with_thresholds()

                # If global threshold is set, also check devices without individual thresholds
                devices = devices_with_thresholds
                if global_threshold and global_threshold > 0:
                    all_active = await device_repo.get_all_active()
                    devices_with_threshold_ids = {d.id for d in devices_with_thresholds}
                    devices_without_thresholds = [
                        d for d in all_active if d.id not in devices_with_threshold_ids
                    ]
                    devices = devices_with_thresholds + devices_without_thresholds

                if not devices:
                    self.logger.debug("No devices with bandwidth thresholds configured")
                    return {
                        "devices_checked": 0,
                        "thresholds_breached": 0,
                        "devices_deactivated": 0,
                    }

                self.logger.info(f"Checking bandwidth thresholds for {len(devices)} devices")

                thresholds_breached = 0
                devices_deactivated = 0

                for device in devices:
                    try:
                        breached, auto_deactivate, threshold = await self._check_device_threshold(
                            session,
                            device,
                            device_repo,
                            bandwidth_repo,
                            global_threshold,
                            global_auto_deactivate,
                            global_time_window,
                        )
                        if breached:
                            thresholds_breached += 1

                            # Auto-deactivate if enabled (device setting or global setting)
                            if auto_deactivate:
                                await self._deactivate_device(
                                    session, device, device_repo, threshold
                                )
                                devices_deactivated += 1

                    except Exception as e:
                        self.logger.error(
                            f"Error checking threshold for device {device.id} ({device.ip_address}): {e}",
                            exc_info=True,
                        )

                self.logger.info(
                    f"Threshold check complete: {len(devices)} checked, "
                    f"{thresholds_breached} breached, {devices_deactivated} deactivated"
                )

                return {
                    "devices_checked": len(devices),
                    "thresholds_breached": thresholds_breached,
                    "devices_deactivated": devices_deactivated,
                }

            finally:
                await session.close()

    async def _check_device_threshold(
        self,
        session: AsyncSession,
        device: Device,
        device_repo: DeviceRepository,
        bandwidth_repo: BandwidthUsageRepository,
        global_threshold: float | None = None,
        global_auto_deactivate: bool = False,
        global_time_window: int = 5,
    ) -> tuple[bool, bool, float]:
        """
        Check if a device has exceeded its bandwidth threshold.

        Args:
            session: Database session
            device: Device to check
            device_repo: Device repository
            bandwidth_repo: Bandwidth repository
            global_threshold: Global threshold to use as fallback
            global_auto_deactivate: Global auto-deactivate setting
            global_time_window: Global time window setting

        Returns:
            Tuple of (threshold_breached, auto_deactivate, threshold_value)
        """
        # Use device threshold if set, otherwise use global threshold
        threshold = device.bandwidth_threshold_mbps
        auto_deactivate = device.auto_deactivate_on_threshold
        time_window = device.threshold_time_window_minutes

        if not threshold or threshold <= 0:
            if global_threshold and global_threshold > 0:
                threshold = global_threshold
                auto_deactivate = global_auto_deactivate
                time_window = global_time_window
            else:
                return False, False, 0.0

        # Skip if already deactivated
        if device.status == DeviceStatus.DEACTIVATED:
            return False, False, 0.0

        # Calculate bandwidth usage over time window
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=time_window)

        usage_records = await bandwidth_repo.get_by_time_range(device.id, start_time, now)

        if not usage_records:
            self.logger.debug(f"No bandwidth data for device {device.id}")
            return False, False, 0.0

        # Calculate average bandwidth in Mbps
        total_bytes = sum(r.bytes_sent + r.bytes_received for r in usage_records)
        time_span_seconds = time_window * 60

        if time_span_seconds <= 0:
            return False, False, 0.0

        # Convert bytes to Mbps: (bytes * 8) / (seconds * 1,000,000)
        avg_mbps = (total_bytes * 8) / (time_span_seconds * 1_000_000)

        self.logger.debug(
            f"Device {device.ip_address}: {avg_mbps:.2f} Mbps (threshold: {threshold:.2f} Mbps)"
        )

        # Check if threshold exceeded
        if avg_mbps > threshold:
            self.logger.warning(
                f"Bandwidth threshold exceeded for device {device.hostname} ({device.ip_address}): "
                f"{avg_mbps:.2f} Mbps > {threshold:.2f} Mbps"
            )

            # Update breach count and timestamp
            await device_repo.update(
                device.id,
                {
                    "threshold_breach_count": device.threshold_breach_count + 1,
                    "last_threshold_breach": now,
                },
            )

            # Send alert to admin users
            await self._send_threshold_alert(session, device, avg_mbps)

            return True, auto_deactivate, threshold

        return False, auto_deactivate, threshold

    async def _deactivate_device(
        self,
        session: AsyncSession,
        device: Device,
        device_repo: DeviceRepository,
        threshold: float,
    ) -> None:
        """
        Auto-deactivate a device that exceeded its threshold.

        Args:
            session: Database session
            device: Device to deactivate
            device_repo: Device repository
        """
        self.logger.warning(
            f"Auto-deactivating device {device.hostname} ({device.ip_address}) "
            f"due to bandwidth threshold breach"
        )

        try:
            # Block the device at network level
            await self.bandwidth_controller.block_device(device.ip_address)

            # Update device status
            await device_repo.update(
                device.id,
                {
                    "status": DeviceStatus.DEACTIVATED,
                    "is_blocked": True,
                },
            )

            # Log block history
            from src.models.device import BlockHistory

            block_record = BlockHistory(
                device_id=device.id,
                action="auto_block",
                reason=f"Auto-deactivated: Bandwidth threshold ({threshold} Mbps) exceeded",
                created_by="system_threshold_monitor",
            )
            session.add(block_record)
            await session.commit()

            self.logger.info(f"Device {device.ip_address} successfully deactivated")

        except Exception as e:
            self.logger.error(
                f"Failed to deactivate device {device.ip_address}: {e}", exc_info=True
            )
            raise

    async def _send_threshold_alert(
        self,
        session: AsyncSession,
        device: Device,
        current_mbps: float,
    ) -> None:
        """
        Send threshold breach alert to admin users.

        Args:
            session: Database session
            device: Device that breached threshold
            current_mbps: Current bandwidth usage in Mbps
        """
        try:
            user_repo = UserRepository(session)

            # Get all admin users
            admin_users = await user_repo.get_admin_users()

            if not admin_users:
                self.logger.warning("No admin users found to send threshold alert")
                return

            # Prepare alert details
            alert_data = {
                "device_id": device.id,
                "device_hostname": device.hostname or "Unknown",
                "device_ip": device.ip_address,
                "current_usage_mbps": round(current_mbps, 2),
                "threshold_mbps": device.bandwidth_threshold_mbps,
                "time_window_minutes": device.threshold_time_window_minutes,
                "breach_count": device.threshold_breach_count + 1,
                "auto_deactivate_enabled": device.auto_deactivate_on_threshold,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Generate message
            message = self._generate_alert_message(alert_data)

            # Send notifications to each admin
            for admin in admin_users:
                try:
                    # Send via available channels
                    await self.notification_manager.send_threshold_alert(
                        admin_email=admin.email,
                        admin_username=admin.username,
                        alert_data=alert_data,
                        message=message,
                    )

                    self.logger.info(f"Threshold alert sent to admin: {admin.username}")

                except Exception as e:
                    self.logger.error(
                        f"Failed to send threshold alert to admin {admin.username}: {e}",
                        exc_info=True,
                    )

        except Exception as e:
            self.logger.error(f"Error sending threshold alerts: {e}", exc_info=True)

    def _generate_alert_message(self, alert_data: dict[str, Any]) -> str:
        """
        Generate human-readable alert message.

        Args:
            alert_data: Alert data dictionary

        Returns:
            Formatted alert message
        """
        device_name = alert_data["device_hostname"]
        device_ip = alert_data["device_ip"]
        current = alert_data["current_usage_mbps"]
        threshold = alert_data["threshold_mbps"]
        time_window = alert_data["time_window_minutes"]
        breach_count = alert_data["breach_count"]
        auto_deactivate = alert_data["auto_deactivate_enabled"]

        message = (
            f"⚠️ BANDWIDTH THRESHOLD BREACH ALERT ⚠️\n\n"
            f"Device: {device_name} ({device_ip})\n"
            f"Current Usage: {current:.2f} Mbps\n"
            f"Threshold: {threshold:.2f} Mbps\n"
            f"Time Window: {time_window} minutes\n"
            f"Breach Count: {breach_count}\n"
        )

        if auto_deactivate:
            message += "\n🚫 Device has been AUTO-DEACTIVATED\n"
        else:
            message += "\n⚠️ Auto-deactivation is DISABLED for this device\n"

        message += "\nPlease review device activity and take appropriate action."

        return message

    async def check_device_now(self, device_id: int) -> dict[str, Any]:
        """
        Manually trigger threshold check for a specific device.

        Args:
            device_id: Device ID to check

        Returns:
            Check result with current usage and threshold status
        """
        async for session in get_db():
            try:
                device_repo = DeviceRepository(session)
                bandwidth_repo = BandwidthUsageRepository(session)

                device = await device_repo.get(device_id)
                if not device:
                    return {"error": f"Device {device_id} not found"}

                if not device.bandwidth_threshold_mbps:
                    return {
                        "device_id": device_id,
                        "threshold_configured": False,
                        "message": "No bandwidth threshold configured for this device",
                    }

                # Check threshold
                breached, _, _ = await self._check_device_threshold(
                    session, device, device_repo, bandwidth_repo
                )

                # Get current usage
                now = datetime.utcnow()
                start_time = now - timedelta(minutes=device.threshold_time_window_minutes)
                usage_records = await bandwidth_repo.get_by_time_range(device.id, start_time, now)

                current_mbps = 0.0
                if usage_records:
                    total_bytes = sum(r.bytes_sent + r.bytes_received for r in usage_records)
                    time_span_seconds = device.threshold_time_window_minutes * 60
                    if time_span_seconds > 0:
                        current_mbps = (total_bytes * 8) / (time_span_seconds * 1_000_000)

                return {
                    "device_id": device_id,
                    "device_hostname": device.hostname,
                    "device_ip": device.ip_address,
                    "threshold_configured": True,
                    "current_usage_mbps": round(current_mbps, 2),
                    "threshold_mbps": device.bandwidth_threshold_mbps,
                    "time_window_minutes": device.threshold_time_window_minutes,
                    "threshold_breached": breached,
                    "auto_deactivate_enabled": device.auto_deactivate_on_threshold,
                    "breach_count": device.threshold_breach_count,
                    "last_breach": device.last_threshold_breach.isoformat()
                    if device.last_threshold_breach
                    else None,
                }

            finally:
                await session.close()


# Global instance
_threshold_monitor: BandwidthThresholdMonitor | None = None


def get_threshold_monitor() -> BandwidthThresholdMonitor:
    """Get the global threshold monitor instance."""
    global _threshold_monitor
    if _threshold_monitor is None:
        _threshold_monitor = BandwidthThresholdMonitor()
    return _threshold_monitor
