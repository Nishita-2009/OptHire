"""
Skill Gap Analysis Endpoint (Agent 4).
"""
import logging
from fastapi import APIRouter, HTTPException, status

from agents.skill_gap.parser import analyze_skill_gap
from schemas.common import ErrorResponse
from schemas.skill_gap import SkillGapRequest, SkillGapResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skill-gap", tags=["Skill Gap"])


@router.post(
    "",
    response_model=SkillGapResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or missing input parameters"},
        502: {"model": ErrorResponse, "description": "Upstream AI skill gap analysis error"},
    },
    summary="Analyze Candidate Skill Gaps",
    description="Identifies missing technical skills and generates a tailored learning path using Agent 4 (Skill Gap Analyzer).",
)
def analyze_skill_gap_endpoint(request: SkillGapRequest) -> SkillGapResponse:
    if not request.resume or not isinstance(request.resume, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid resume payload is required.",
        )
    if not request.job_description or not isinstance(request.job_description, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid job_description payload is required.",
        )
    if not request.match_result or not isinstance(request.match_result, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid match_result payload is required.",
        )

    try:
        gap_report = analyze_skill_gap(
            request.resume,
            request.job_description,
            request.match_result,
        )
    except ValueError as exc:
        logger.error("Agent 4 failed to analyze skill gap: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI skill gap analysis returned an invalid response structure.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 4: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error during skill gap analysis.",
        ) from exc

    return SkillGapResponse.model_validate(gap_report)

