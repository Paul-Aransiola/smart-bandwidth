"""
Main FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import devices, health, stats
from src.core.config import get_settings
from src.core.database import close_db, init_db
from src.core.exceptions import BandwidthMonitorException
from src.utils.logger import get_logger, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Smart Bandwidth Monitor API")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Smart Bandwidth Monitor API")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


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


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Smart Bandwidth Monitor & Control API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
