"""
Reporting and analytics API routes.
"""

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.reporting import (
    BandwidthTrend,
    ReportExportRequest,
    ReportExportResponse,
    TopConsumer,
    UsageReport,
)
from src.schemas.response import success_response
from src.services.reporting_service import ReportingService
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/reports")


@router.get(
    "/usage",
    response_model=dict,
    summary="Get bandwidth usage report",
    responses={
        200: {"description": "Usage report generated successfully"},
        400: {"description": "Invalid date range"},
        404: {"description": "Device not found"},
    },
)
async def get_usage_report(
    start_date: datetime = Query(..., description="Start date for report (ISO 8601 format)"),
    end_date: datetime = Query(..., description="End date for report (ISO 8601 format)"),
    device_id: int | None = Query(
        None, description="Optional device ID for device-specific report"
    ),
    top_n: int = Query(10, ge=1, le=50, description="Number of top consumers to include"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate comprehensive bandwidth usage report.

    Returns network-wide or device-specific bandwidth usage statistics including
    total bytes transferred, active devices, and top consumers.
    """
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        reporting_service = ReportingService(db)
        report = await reporting_service.generate_usage_report(
            start_date, end_date, device_id, top_n
        )

        return success_response(
            data=report.model_dump(),
            message="Usage report generated successfully",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error generating usage report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate usage report",
        ) from e


@router.get(
    "/trends",
    response_model=dict,
    summary="Get bandwidth trends",
    responses={
        200: {"description": "Bandwidth trends retrieved successfully"},
        400: {"description": "Invalid parameters"},
    },
)
async def get_bandwidth_trends(
    start_date: datetime = Query(..., description="Start date for trends (ISO 8601 format)"),
    end_date: datetime = Query(..., description="End date for trends (ISO 8601 format)"),
    interval: Literal["hour", "day", "week"] = Query("day", description="Aggregation interval"),
    device_id: int | None = Query(None, description="Optional device ID to filter by"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get bandwidth usage trends over time.

    Returns time-series data showing bandwidth usage patterns aggregated by
    the specified interval (hour, day, or week).
    """
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        reporting_service = ReportingService(db)
        trends = await reporting_service.get_bandwidth_trends(
            start_date, end_date, interval, device_id
        )

        return success_response(
            data=trends.model_dump(),
            message="Bandwidth trends retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting bandwidth trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bandwidth trends",
        ) from e


@router.get(
    "/top-consumers",
    response_model=dict,
    summary="Get top bandwidth consumers",
    responses={
        200: {"description": "Top consumers retrieved successfully"},
        400: {"description": "Invalid parameters"},
    },
)
async def get_top_consumers(
    start_date: datetime = Query(..., description="Start date for analysis (ISO 8601 format)"),
    end_date: datetime = Query(..., description="End date for analysis (ISO 8601 format)"),
    limit: int = Query(10, ge=1, le=100, description="Number of top consumers to return"),
    order_by: Literal["sent", "received", "total"] = Query(
        "total", description="Order by sent, received, or total bytes"
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get top bandwidth consumers.

    Returns a list of devices that consumed the most bandwidth in the specified
    period, ordered by the selected metric.
    """
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        reporting_service = ReportingService(db)
        consumers = await reporting_service.get_top_consumers(start_date, end_date, limit, order_by)

        return success_response(
            data=[c.model_dump() for c in consumers],
            message=f"Top {len(consumers)} consumers retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting top consumers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top consumers",
        ) from e


@router.post(
    "/export",
    response_model=dict,
    summary="Export report to file",
    responses={
        200: {"description": "Report exported successfully"},
        400: {"description": "Invalid export parameters"},
    },
)
async def export_report(
    request: ReportExportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Export report to CSV or JSON format.

    Generates a downloadable file containing the requested report data
    in the specified format.
    """
    try:
        if request.start_date >= request.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        reporting_service = ReportingService(db)
        export_response = await reporting_service.export_report(request)

        return success_response(
            data=export_response.model_dump(),
            message=f"Report exported successfully to {export_response.filename}",
        )
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export report",
        ) from e


@router.get(
    "/download/{filename}",
    summary="Download exported report",
    responses={
        200: {"description": "File downloaded successfully"},
        404: {"description": "File not found"},
    },
)
async def download_report(filename: str) -> FileResponse:
    """
    Download an exported report file.

    Returns the exported report file for download.
    """
    from pathlib import Path

    exports_dir = Path("exports")
    filepath = exports_dir / filename

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found",
        )

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get(
    "/quick-stats",
    response_model=dict,
    summary="Get quick statistics",
    responses={
        200: {"description": "Quick statistics retrieved successfully"},
    },
)
async def get_quick_stats(
    period: Literal["24h", "7d", "30d"] = Query("24h", description="Time period for statistics"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get quick bandwidth statistics for common time periods.

    Provides a convenient endpoint for getting statistics for the last
    24 hours, 7 days, or 30 days.
    """
    try:
        # Calculate date range based on period
        end_date = datetime.now()
        if period == "24h":
            start_date = end_date - timedelta(hours=24)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        else:  # 30d
            start_date = end_date - timedelta(days=30)

        reporting_service = ReportingService(db)
        report = await reporting_service.generate_usage_report(
            start_date, end_date, device_id=None, top_n=5
        )

        return success_response(
            data={
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "statistics": report.model_dump(),
            },
            message=f"Statistics for {period} retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        ) from e
