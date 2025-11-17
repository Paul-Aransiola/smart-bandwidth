"""
Configuration management using Pydantic Settings.
Follows the Single Responsibility Principle.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: str = Field(
        default="development", description="Environment: development, staging, production"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="Enable auto-reload in development")
    api_title: str = Field(default="Smart Bandwidth Monitor API", description="API title")
    api_version: str = Field(default="0.1.0", description="API version")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./bandwidth_monitor.db", description="Database connection URL"
    )

    # Security
    secret_key: str = Field(
        default="change-this-secret-key-in-production", description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/app.log", description="Log file path")
    log_max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    log_backup_count: int = Field(default=5, description="Number of log backup files")

    # Network Monitoring
    network_interface: str = Field(default="eth0", description="Network interface to monitor")
    monitor_interval: int = Field(default=5, description="Monitoring interval in seconds")
    packet_capture_timeout: int = Field(default=10, description="Packet capture timeout in seconds")
    capture_filter: str = Field(default="", description="BPF filter for packet capture")

    # Bandwidth Control
    max_bandwidth_mbps: int = Field(default=100, description="Maximum bandwidth in Mbps")
    default_throttle_mbps: int = Field(default=10, description="Default throttle limit in Mbps")
    enable_blocking: bool = Field(default=True, description="Enable device blocking")
    enable_throttling: bool = Field(default=True, description="Enable bandwidth throttling")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v_lower

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure singleton pattern.
    """
    return Settings()
