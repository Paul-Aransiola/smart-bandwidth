"""
Main FastAPI application.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import alerts, control, devices, health, reports, stats, websocket
from src.core.config import get_settings
from src.core.database import close_db, get_db, init_db
from src.core.exceptions import BandwidthMonitorException
from src.schemas.response import error_response, success_response
from src.services.network_monitor import NetworkMonitor
from src.services.websocket_manager import manager as ws_manager
from src.utils.logger import get_logger, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Global network monitor instance
network_monitor: NetworkMonitor | None = None
monitoring_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    global network_monitor, monitoring_task

    # Startup
    logger.info("Starting Smart Bandwidth Monitor API")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Start network monitoring if enabled
    if settings.enable_monitoring:
        try:
            network_monitor = NetworkMonitor(settings.network_interface)
            await network_monitor.start()
            logger.info("Network monitoring started")

            # Start background task to periodically save bandwidth data
            monitoring_task = asyncio.create_task(periodic_bandwidth_save())
            logger.info("Background bandwidth saving task started")
        except Exception as e:
            logger.warning(f"Failed to start network monitoring: {e}")
            logger.warning("Continuing without network monitoring...")

    yield

    # Shutdown
    logger.info("Shutting down Smart Bandwidth Monitor API")

    # Stop monitoring task
    if monitoring_task and not monitoring_task.done():
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Background monitoring task cancelled")

    # Stop network monitor
    if network_monitor:
        try:
            await network_monitor.stop()
            logger.info("Network monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping network monitor: {e}")

    # Close database
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


async def periodic_bandwidth_save():
    """
    Background task that periodically saves bandwidth data to the database.
    Runs every MONITORING_INTERVAL seconds.
    """
    from datetime import datetime

    from src.core.database import AsyncSessionLocal
    from src.models.device import BandwidthUsage, Device
    from src.repositories.bandwidth_repository import BandwidthUsageRepository
    from src.repositories.device_repository import DeviceRepository
    from src.services.alert_service import AlertService
    from src.services.notification_handlers import NotificationManager

    logger.info("Starting periodic bandwidth save task")

    # Initialize notification manager with WebSocket support
    notification_manager = NotificationManager(websocket_manager=ws_manager)

    while True:
        try:
            await asyncio.sleep(settings.monitoring_interval)

            if not network_monitor or not network_monitor.is_running:
                continue

            # Get all device stats from network monitor
            stats = network_monitor.get_all_stats()

            if not stats:
                logger.debug("No bandwidth data to save")
                continue

            # Save to database
            async with AsyncSessionLocal() as session:
                device_repo = DeviceRepository(session)
                bandwidth_repo = BandwidthUsageRepository(session)

                for stat in stats:
                    ip_address = stat["ip_address"]
                    bytes_sent = stat["bytes_sent"]
                    bytes_received = stat["bytes_received"]

                    # Skip if no traffic
                    if bytes_sent == 0 and bytes_received == 0:
                        continue

                    # Find or create device
                    device = await device_repo.get_by_ip(ip_address)
                    if not device:
                        # Create new device
                        device = Device(
                            ip_address=ip_address,
                            mac_address="",  # Will be populated later
                            hostname="",
                            device_name=f"Device {ip_address}",
                            status="active",
                            first_seen=datetime.now(),
                            last_seen=datetime.now(),
                            is_blocked=False,
                            is_throttled=False,
                            total_bytes_sent=0,
                            total_bytes_received=0,
                        )
                        device = await device_repo.create(device)
                        logger.info(f"Created new device: {ip_address}")

                    # Update device bandwidth totals
                    device.total_bytes_sent += bytes_sent
                    device.total_bytes_received += bytes_received
                    device.last_seen = datetime.now()
                    await device_repo.update(device)

                    # Create bandwidth usage record
                    bandwidth_record = BandwidthUsage(
                        device_id=device.id,
                        bytes_sent=bytes_sent,
                        bytes_received=bytes_received,
                        timestamp=datetime.now(),
                    )
                    await bandwidth_repo.create(bandwidth_record)

                await session.commit()
                logger.debug(f"Saved bandwidth data for {len(stats)} devices")

                # Broadcast bandwidth stats via WebSocket
                await ws_manager.broadcast_bandwidth_stats(
                    {
                        "total_devices": len(stats),
                        "devices": stats,
                    }
                )

            # Evaluate alert rules after saving bandwidth data
            try:
                async with AsyncSessionLocal() as alert_session:
                    alert_service = AlertService(
                        alert_session, notification_manager=notification_manager
                    )
                    results = await alert_service.evaluate_all_rules()
                    if results["alerts_triggered"] > 0:
                        logger.info(
                            f"Alert evaluation: {results['rules_checked']} rules checked, "
                            f"{results['alerts_triggered']} alerts triggered"
                        )
                    await alert_session.commit()
            except Exception as alert_error:
                logger.error(f"Error evaluating alert rules: {alert_error}", exc_info=True)

        except asyncio.CancelledError:
            logger.info("Bandwidth save task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in bandwidth save task: {e}")
            # Continue running despite errors
            await asyncio.sleep(10)  # Wait a bit before retrying


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    Smart Bandwidth Monitor & Control API
    
    A lightweight backend system for monitoring and controlling bandwidth usage
    in shared Wi-Fi networks.
    
    ## Features
    
    * **Real-time Monitoring**: Track bandwidth usage per device (IP/MAC)
    * **Device Management**: Identify and manage connected devices
    * **Bandwidth Control**: Block or throttle high-usage devices
    * **Statistics**: View detailed bandwidth statistics and trends
    
    ## Authentication
    
    Some endpoints require authentication. Use the `/api/v1/auth/login` endpoint
    to obtain an access token.
    
    ## Rate Limiting
    
    API requests are rate-limited to prevent abuse. Check response headers for
    rate limit information.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(BandwidthMonitorException)
async def bandwidth_monitor_exception_handler(request, exc: BandwidthMonitorException):
    """Handle custom exceptions."""
    logger.error(f"Exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
        },
    )


# Include routers
app.include_router(health.router, prefix=settings.api_prefix, tags=["Health"])
app.include_router(devices.router, prefix=settings.api_prefix, tags=["Devices"])
app.include_router(stats.router, prefix=settings.api_prefix, tags=["Statistics"])
app.include_router(reports.router, prefix=settings.api_prefix, tags=["Reports"])
app.include_router(alerts.router, prefix=settings.api_prefix, tags=["Alerts"])
app.include_router(control.router, prefix=settings.api_prefix, tags=["Control"])
app.include_router(websocket.router, tags=["WebSocket"])

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return success_response(
        data={
            "name": "Smart Bandwidth Monitor & Control API",
            "version": settings.api_version,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
        },
        message="Welcome to Smart Bandwidth Monitor API",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
