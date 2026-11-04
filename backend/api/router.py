"""
Central API Router for OptHire.
Assembles all versioned endpoint routers.
"""
from fastapi import APIRouter
from api.routes import (
    health,
    resumes,
    jobs,
    match,
    skill_gap,
    interview,
    reports,
    pipeline,
)

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers under /api/v1
api_v1_router.include_router(resumes.router)
api_v1_router.include_router(jobs.router)
api_v1_router.include_router(match.router)
api_v1_router.include_router(skill_gap.router)
api_v1_router.include_router(interview.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(pipeline.router)

# Root level router
root_router = APIRouter()
root_router.include_router(health.router)
root_router.include_router(api_v1_router)

__all__ = ["root_router", "api_v1_router"]
