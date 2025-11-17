"""Health check endpoints."""

from fastapi import APIRouter

from src.core.config import get_settings
from src.schemas.response import success_response

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns API status and version information.
    """
    return success_response(
        data={
            "status": "healthy",
            "version": settings.api_version,
            "environment": settings.env,
        },
        message="API is healthy",
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint.

    Returns comprehensive health information including database, services, etc.
    """
    # TODO: Add checks for database, network monitor, bandwidth controller
    return success_response(
        data={
            "status": "healthy",
            "version": settings.api_version,
            "environment": settings.env,
            "services": {
                "database": "connected",
                "network_monitor": "ready",
                "bandwidth_controller": "ready",
            },
        },
        message="All services are healthy",
    )
