"""
Common schemas: health check and standardized API error response.
"""
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """API health status response."""
    status: str = Field(default="ok", description="Operational status of the service")
    app: str = Field(default="OptHire API", description="Application name")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Standardized API error response format."""
    error: str = Field(..., description="High-level error category or summary")
    message: str = Field(..., description="Human-readable description of what went wrong")
    detail: Optional[Any] = Field(default=None, description="Optional diagnostic details or validation errors")
    code: int = Field(default=400, description="HTTP status code")

    model_config = ConfigDict(extra="allow")
