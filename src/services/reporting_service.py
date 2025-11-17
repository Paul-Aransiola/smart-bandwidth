"""
Service for generating bandwidth usage reports and analytics.
"""

import csv
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.bandwidth_repository import BandwidthUsageRepository
from src.repositories.device_repository import DeviceRepository
from src.schemas.reporting import (
    BandwidthTrend,
    ReportExportRequest,
    ReportExportResponse,
    TimeSeriesDataPoint,
    TopConsumer,
    UsageReport,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportingService:
    """Service for generating bandwidth reports and analytics."""

    def __init__(self, session: AsyncSession):
        """Initialize reporting service."""
        self.session = session
        self.bandwidth_repo = BandwidthUsageRepository(session)
        self.device_repo = DeviceRepository(session)
        self.exports_dir = Path("exports")
        self.exports_dir.mkdir(exist_ok=True)

    async def generate_usage_report(
        self,
        start_date: datetime,
        end_date: datetime,
        device_id: int | None = None,
        top_n: int = 10,
    ) -> UsageReport:
        """
        Generate comprehensive bandwidth usage report.

        Args:
            start_date: Start of report period
            end_date: End of report period
            device_id: Optional device ID for device-specific report
            top_n: Number of top consumers to include

        Returns:
            UsageReport with comprehensive statistics
        """
        logger.info(f"Generating usage report from {start_date} to {end_date}")

        if device_id:
            # Device-specific report
            device = await self.device_repo.get(device_id)
            if not device:
                raise ValueError(f"Device with ID {device_id} not found")

            usage_records = await self.bandwidth_repo.get_usage_by_date_range(
                start_date, end_date, device_id
            )

            total_sent = sum(r.bytes_sent for r in usage_records)
            total_received = sum(r.bytes_received for r in usage_records)

            return UsageReport(
                report_type="device",
                start_date=start_date,
                end_date=end_date,
                total_devices=1,
                active_devices=1 if device.status == "active" else 0,
                total_bytes_sent=total_sent,
                total_bytes_received=total_received,
                total_bytes=total_sent + total_received,
                top_consumers=[],
                device_id=device.id,
                device_ip=device.ip_address,
                device_name=device.device_name,
            )
        else:
            # Network-wide report
            all_devices = await self.device_repo.list()
            active_devices = [d for d in all_devices if d.status == "active"]

            # Get top consumers
            top_consumers_data = await self.bandwidth_repo.get_top_consumers(
                start_date, end_date, limit=top_n
            )

            # Calculate total bandwidth
            total_sent = sum(tc["total_bytes_sent"] for tc in top_consumers_data)
            total_received = sum(tc["total_bytes_received"] for tc in top_consumers_data)
            total_bytes = total_sent + total_received

            # Enrich top consumers with device info
            top_consumers = []
            for tc_data in top_consumers_data:
                device = await self.device_repo.get(tc_data["device_id"])
                if device:
                    percentage = (
                        (tc_data["total_bytes"] / total_bytes * 100) if total_bytes > 0 else 0.0
                    )
                    top_consumers.append(
                        TopConsumer(
                            device_id=device.id,
                            device_ip=device.ip_address,
                            device_name=device.device_name,
                            device_status=device.status,
                            total_bytes_sent=tc_data["total_bytes_sent"],
                            total_bytes_received=tc_data["total_bytes_received"],
                            total_bytes=tc_data["total_bytes"],
                            avg_upload_speed_mbps=tc_data["avg_upload_speed_mbps"],
                            avg_download_speed_mbps=tc_data["avg_download_speed_mbps"],
                            percentage_of_total=percentage,
                        )
                    )

            return UsageReport(
                report_type="network",
                start_date=start_date,
                end_date=end_date,
                total_devices=len(all_devices),
                active_devices=len(active_devices),
                total_bytes_sent=total_sent,
                total_bytes_received=total_received,
                total_bytes=total_bytes,
                top_consumers=top_consumers,
            )

    async def get_bandwidth_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: Literal["hour", "day", "week"] = "day",
        device_id: int | None = None,
    ) -> BandwidthTrend:
        """
        Get bandwidth usage trends over time.

        Args:
            start_date: Start of trend period
            end_date: End of trend period
            interval: Aggregation interval (hour, day, week)
            device_id: Optional device ID to filter by

        Returns:
            BandwidthTrend with time series data
        """
        logger.info(f"Generating bandwidth trends from {start_date} to {end_date} ({interval})")

        # Get aggregated data
        aggregated_data = await self.bandwidth_repo.get_aggregated_usage(
            start_date, end_date, interval, device_id
        )

        # Convert to TimeSeriesDataPoint objects
        data_points = [TimeSeriesDataPoint(**dp) for dp in aggregated_data]

        # Calculate totals
        total_sent = sum(dp.total_bytes_sent for dp in data_points)
        total_received = sum(dp.total_bytes_received for dp in data_points)

        # Get device info if specified
        device_ip = None
        device_name = None
        if device_id:
            device = await self.device_repo.get(device_id)
            if device:
                device_ip = device.ip_address
                device_name = device.device_name

        return BandwidthTrend(
            device_id=device_id,
            device_ip=device_ip,
            device_name=device_name,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            data_points=data_points,
            total_bytes_sent=total_sent,
            total_bytes_received=total_received,
            total_bytes=total_sent + total_received,
        )

    async def get_top_consumers(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
        order_by: Literal["sent", "received", "total"] = "total",
    ) -> list[TopConsumer]:
        """
        Get top bandwidth consumers.

        Args:
            start_date: Start of period
            end_date: End of period
            limit: Number of top consumers to return
            order_by: Order by sent, received, or total bytes

        Returns:
            List of TopConsumer objects
        """
        logger.info(f"Getting top {limit} consumers from {start_date} to {end_date}")

        # Get top consumers data
        top_consumers_data = await self.bandwidth_repo.get_top_consumers(
            start_date, end_date, limit, order_by
        )

        # Calculate total for percentages
        total_bytes = sum(tc["total_bytes"] for tc in top_consumers_data)

        # Enrich with device info
        top_consumers = []
        for tc_data in top_consumers_data:
            device = await self.device_repo.get(tc_data["device_id"])
            if device:
                percentage = (
                    (tc_data["total_bytes"] / total_bytes * 100) if total_bytes > 0 else 0.0
                )
                top_consumers.append(
                    TopConsumer(
                        device_id=device.id,
                        device_ip=device.ip_address,
                        device_name=device.device_name,
                        device_status=device.status,
                        total_bytes_sent=tc_data["total_bytes_sent"],
                        total_bytes_received=tc_data["total_bytes_received"],
                        total_bytes=tc_data["total_bytes"],
                        avg_upload_speed_mbps=tc_data["avg_upload_speed_mbps"],
                        avg_download_speed_mbps=tc_data["avg_download_speed_mbps"],
                        percentage_of_total=percentage,
                    )
                )

        return top_consumers

    async def export_report(self, request: ReportExportRequest) -> ReportExportResponse:
        """
        Export report to CSV or JSON format.

        Args:
            request: Export request parameters

        Returns:
            ReportExportResponse with export details
        """
        logger.info(f"Exporting {request.report_type} report in {request.format} format")

        # Generate report data based on type
        if request.report_type == "usage":
            report = await self.generate_usage_report(
                request.start_date, request.end_date, request.device_id
            )
            data = report.model_dump()
            filename_base = "usage_report"
        elif request.report_type == "trends":
            interval = request.interval or "day"
            trends = await self.get_bandwidth_trends(
                request.start_date, request.end_date, interval, request.device_id
            )
            data = trends.model_dump()
            filename_base = "trends_report"
        else:  # top_consumers
            limit = request.limit or 10
            consumers = await self.get_top_consumers(
                request.start_date, request.end_date, limit
            )
            data = [c.model_dump() for c in consumers]
            filename_base = "top_consumers_report"

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_base}_{timestamp}.{request.format}"
        filepath = self.exports_dir / filename

        # Export to file
        if request.format == "csv":
            content, record_count = self._export_to_csv(data, request.report_type)
        else:  # json
            content, record_count = self._export_to_json(data, request.report_type)

        # Write to file
        filepath.write_text(content, encoding="utf-8")
        size_bytes = filepath.stat().st_size

        logger.info(f"Export saved to {filepath} ({size_bytes} bytes)")

        return ReportExportResponse(
            filename=filename,
            format=request.format,
            size_bytes=size_bytes,
            record_count=record_count,
            download_url=f"/api/v1/reports/download/{filename}",
        )

    def _export_to_csv(
        self, data: dict | list, report_type: str
    ) -> tuple[str, int]:
        """Export data to CSV format."""
        output = StringIO()
        writer = csv.writer(output)

        if report_type == "top_consumers":
            # List of consumers
            if not data:
                return "", 0

            # Write header
            headers = list(data[0].keys())
            writer.writerow(headers)

            # Write rows
            for item in data:
                writer.writerow(item.values())

            return output.getvalue(), len(data)
        elif report_type == "trends":
            # Trends with data points
            data_points = data.get("data_points", [])
            if not data_points:
                return "", 0

            # Write metadata
            writer.writerow(["Device ID", data.get("device_id", "All Devices")])
            writer.writerow(["Start Date", data["start_date"]])
            writer.writerow(["End Date", data["end_date"]])
            writer.writerow(["Interval", data["interval"]])
            writer.writerow([])

            # Write data points
            headers = list(data_points[0].keys())
            writer.writerow(headers)
            for dp in data_points:
                writer.writerow(dp.values())

            return output.getvalue(), len(data_points)
        else:  # usage
            # Usage report with top consumers
            writer.writerow(["Usage Report"])
            writer.writerow(["Report Type", data["report_type"]])
            writer.writerow(["Start Date", data["start_date"]])
            writer.writerow(["End Date", data["end_date"]])
            writer.writerow(["Total Devices", data["total_devices"]])
            writer.writerow(["Active Devices", data["active_devices"]])
            writer.writerow(["Total Bytes Sent", data["total_bytes_sent"]])
            writer.writerow(["Total Bytes Received", data["total_bytes_received"]])
            writer.writerow([])

            top_consumers = data.get("top_consumers", [])
            if top_consumers:
                writer.writerow(["Top Consumers"])
                headers = list(top_consumers[0].keys())
                writer.writerow(headers)
                for tc in top_consumers:
                    writer.writerow(tc.values())

            return output.getvalue(), len(top_consumers)

    def _export_to_json(
        self, data: dict | list, report_type: str
    ) -> tuple[str, int]:
        """Export data to JSON format."""
        # Convert datetime objects to ISO format strings
        json_str = json.dumps(data, indent=2, default=str)

        if isinstance(data, list):
            record_count = len(data)
        elif report_type == "trends":
            record_count = len(data.get("data_points", []))
        elif report_type == "usage":
            record_count = len(data.get("top_consumers", []))
        else:
            record_count = 1

        return json_str, record_count
