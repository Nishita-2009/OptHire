"""
Health check route.
"""
from fastapi import APIRouter, status
from schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="API Health Check",
    description="Returns the operational status of the OptHire backend without consuming AI quota.",
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app="OptHire API",
        version="1.0.0",
    )

