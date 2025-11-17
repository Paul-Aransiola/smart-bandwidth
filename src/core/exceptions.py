"""
Custom exceptions for the application.
Follows proper exception hierarchy.
"""


class BandwidthMonitorException(Exception):
    """Base exception for all custom exceptions."""

    def __init__(self, message: str, status_code: int = 500):
        """Initialize exception with message and status code."""
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DeviceNotFoundException(BandwidthMonitorException):
    """Raised when a device is not found."""

    def __init__(self, identifier: str):
        """Initialize exception with device identifier."""
        super().__init__(
            message=f"Device with identifier '{identifier}' not found",
            status_code=404,
        )


class DeviceAlreadyExistsException(BandwidthMonitorException):
    """Raised when attempting to create a device that already exists."""

    def __init__(self, identifier: str):
        """Initialize exception with device identifier."""
        super().__init__(
            message=f"Device with identifier '{identifier}' already exists",
            status_code=409,
        )


class NetworkMonitorException(BandwidthMonitorException):
    """Raised when network monitoring fails."""

    def __init__(self, message: str):
        """Initialize exception with error message."""
        super().__init__(
            message=f"Network monitoring error: {message}",
            status_code=500,
        )


class BandwidthControlException(BandwidthMonitorException):
    """Raised when bandwidth control operations fail."""

    def __init__(self, message: str):
        """Initialize exception with error message."""
        super().__init__(
            message=f"Bandwidth control error: {message}",
            status_code=500,
        )


class DatabaseException(BandwidthMonitorException):
    """Raised when database operations fail."""

    def __init__(self, message: str):
        """Initialize exception with error message."""
        super().__init__(
            message=f"Database error: {message}",
            status_code=500,
        )


class ValidationException(BandwidthMonitorException):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        """Initialize exception with validation error."""
        super().__init__(
            message=f"Validation error: {message}",
            status_code=422,
        )


class PermissionDeniedException(BandwidthMonitorException):
    """Raised when user lacks permission for an operation."""

    def __init__(self, message: str = "Permission denied"):
        """Initialize exception with permission error."""
        super().__init__(
            message=message,
            status_code=403,
        )


class ConfigurationException(BandwidthMonitorException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str):
        """Initialize exception with configuration error."""
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=500,
        )
