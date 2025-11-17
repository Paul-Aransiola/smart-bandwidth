"""
Standardized API response schemas.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """
    Standardized API response wrapper.

    All API endpoints should return responses in this format for consistency.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Device blocked successfully",
                    "data": {
                        "ip_address": "192.168.1.100",
                        "is_blocked": True,
                    },
                }
            ]
        }
    )

    success: bool = Field(
        description="Whether the operation was successful",
        examples=[True],
    )
    message: str = Field(
        description="Human-readable message describing the result",
        examples=["Operation completed successfully"],
    )
    data: DataT | None = Field(
        default=None,
        description="Response data (type varies by endpoint)",
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": False,
                    "message": "Device not found",
                    "error": "Device with IP 192.168.1.100 not found",
                    "code": "DEVICE_NOT_FOUND",
                }
            ]
        }
    )

    success: bool = Field(
        default=False,
        description="Always false for error responses",
    )
    message: str = Field(
        description="Error message",
        examples=["Device not found"],
    )
    error: str | None = Field(
        default=None,
        description="Detailed error information (optional)",
    )
    code: str | None = Field(
        default=None,
        description="Error code for programmatic handling",
        examples=["DEVICE_NOT_FOUND", "VALIDATION_ERROR"],
    )


class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    Standardized paginated response.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Devices retrieved successfully",
                    "data": [
                        {
                            "id": 1,
                            "ip_address": "192.168.1.100",
                            "is_blocked": False,
                        }
                    ],
                    "pagination": {
                        "total": 100,
                        "count": 1,
                        "skip": 0,
                        "limit": 10,
                        "has_more": True,
                    },
                }
            ]
        }
    )

    success: bool = Field(
        default=True,
        description="Whether the operation was successful",
    )
    message: str = Field(
        default="Data retrieved successfully",
        description="Human-readable message",
    )
    data: list[DataT] = Field(
        description="Array of items",
    )
    pagination: dict[str, Any] = Field(
        description="Pagination metadata",
        examples=[
            {
                "total": 100,
                "count": 10,
                "skip": 0,
                "limit": 10,
                "has_more": True,
            }
        ],
    )


def success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
) -> dict:
    """
    Helper function to create a standardized success response.

    Args:
        data: Response data
        message: Success message

    Returns:
        Dictionary in APIResponse format
    """
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(
    message: str,
    error: str | None = None,
    code: str | None = None,
) -> dict:
    """
    Helper function to create a standardized error response.

    Args:
        message: Error message
        error: Detailed error information
        code: Error code

    Returns:
        Dictionary in ErrorResponse format
    """
    return {
        "success": False,
        "message": message,
        "error": error,
        "code": code,
    }


def paginated_response(
    data: list,
    total: int,
    skip: int,
    limit: int,
    message: str = "Data retrieved successfully",
) -> dict:
    """
    Helper function to create a standardized paginated response.

    Args:
        data: List of items
        total: Total number of items available
        skip: Number of items skipped
        limit: Maximum number of items per page
        message: Success message

    Returns:
        Dictionary in PaginatedResponse format
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "count": len(data),
            "skip": skip,
            "limit": limit,
            "has_more": (skip + len(data)) < total,
        },
    }
