"""Statistics endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device_repository import DeviceRepository
from src.schemas.device import DeviceStatistics
from src.schemas.response import success_response
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def get_network_monitor():
    """Get the global network monitor instance."""
    from src.main import network_monitor

    if not network_monitor:
        raise Exception("Network monitor not initialized")

    return network_monitor


@router.get("/stats")
async def get_overall_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall network statistics.

    Returns aggregated statistics for all devices including total bandwidth usage,
    active devices, blocked devices, etc.
    """
    repo = DeviceRepository(db)
    stats = await repo.get_statistics()

    return success_response(
        data=DeviceStatistics(**stats).model_dump(),
        message="Overall statistics retrieved successfully",
    )


@router.get("/stats/top-consumers")
async def get_top_consumers(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get top bandwidth consumers.

    Returns list of devices consuming the most bandwidth.
    """
    repo = DeviceRepository(db)
    devices = await repo.get_top_consumers(limit=limit)

    data = [
        {
            "id": device.id,
            "ip_address": device.ip_address,
            "mac_address": device.mac_address,
            "device_name": device.device_name,
            "total_bytes": device.total_bytes,
            "total_bytes_sent": device.total_bytes_sent,
            "total_bytes_received": device.total_bytes_received,
        }
        for device in devices
    ]

    return success_response(
        data=data,
        message=f"Top {len(data)} bandwidth consumers retrieved successfully",
    )


@router.get("/stats/protocols")
async def get_protocol_statistics(
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
):
    """
    Get protocol statistics (TCP, UDP, ICMP).

    Returns breakdown of network protocols used by devices.
    """
    try:
        monitor = get_network_monitor()
        stats = monitor.get_protocol_stats(ip_address)

        return success_response(
            data=stats,
            message="Protocol statistics retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting protocol stats: {e}")
        return success_response(
            data={"error": str(e)},
            message="Failed to retrieve protocol statistics",
        )


@router.get("/stats/applications")
async def get_application_statistics(
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
):
    """
    Get application statistics (HTTP, HTTPS, SSH, DNS, etc.).

    Returns breakdown of applications detected from port numbers.
    """
    try:
        monitor = get_network_monitor()
        stats = monitor.get_application_stats(ip_address)

        return success_response(
            data=stats,
            message="Application statistics retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting application stats: {e}")
        return success_response(
            data={"error": str(e)},
            message="Failed to retrieve application statistics",
        )


@router.get("/stats/devices/{ip_address}/dns")
async def get_device_dns_queries(
    ip_address: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of queries to return"),
):
    """
    Get recent DNS queries for a specific device.

    Returns list of domains accessed by the device.
    """
    try:
        monitor = get_network_monitor()
        queries = monitor.get_dns_queries(ip_address, limit)

        # Format timestamps as ISO strings
        formatted_queries = [
            {
                "domain": q["domain"],
                "timestamp": q["timestamp"].isoformat() if q.get("timestamp") else None,
            }
            for q in queries
        ]

        return success_response(
            data={
                "ip_address": ip_address,
                "queries": formatted_queries,
                "total": len(formatted_queries),
            },
            message=f"Retrieved {len(formatted_queries)} DNS queries",
        )
    except Exception as e:
        logger.error(f"Error getting DNS queries: {e}")
        return success_response(
            data={"error": str(e)},
            message="Failed to retrieve DNS queries",
        )


@router.get("/stats/devices/{ip_address}/connections")
async def get_device_connections(
    ip_address: str,
):
    """
    Get active connections for a specific device.

    Returns list of active network connections.
    """
    try:
        monitor = get_network_monitor()
        connections = monitor.get_active_connections(ip_address)

        return success_response(
            data={
                "ip_address": ip_address,
                "connections": connections,
                "total": len(connections),
            },
            message=f"Retrieved {len(connections)} active connections",
        )
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return success_response(
            data={"error": str(e)},
            message="Failed to retrieve connections",
        )


@router.get("/stats/devices/{ip_address}/detailed")
async def get_device_detailed_stats(
    ip_address: str,
):
    """
    Get detailed statistics for a specific device.

    Returns comprehensive statistics including protocols, applications, and connections.
    """
    try:
        monitor = get_network_monitor()
        stats = monitor.get_device_stats(ip_address, include_details=True)

        return success_response(
            data=stats,
            message="Detailed device statistics retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Error getting detailed stats: {e}")
        return success_response(
            data={"error": str(e)},
            message="Failed to retrieve detailed statistics",
        )


@router.get("/stats/top-talkers")
async def get_top_talkers(
    limit: int = Query(10, ge=1, le=100, description="Number of devices to return"),
    metric: str = Query(
        "total_bytes",
        regex="^(total_bytes|bytes_sent|bytes_received|packet_count)$",
        description="Metric to sort by",
    ),
):
    """
    Get top devices by network usage.

    Returns list of most active devices sorted by specified metric.
    """
    try:
        monitor = get_network_monitor()
        devices = monitor.get_top_talkers(limit, metric)

        return success_response(
            data={
                "devices": devices,
                "metric": metric,
                "total": len(devices),
            },
            message=f"Retrieved top {len(devices)} devices by {metric}",
        )
    except Exception as e:
        logger.error(f"Error getting top talkers: {e}")
        return success_response(
            data={"error": str(e)},
            message="Failed to retrieve top talkers",
        )
