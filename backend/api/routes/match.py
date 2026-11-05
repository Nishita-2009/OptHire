"""
Resume Matching Endpoint (Agent 3).
"""
import logging
from fastapi import APIRouter, HTTPException, status

from agents.resume_matcher.parser import match_resume
from schemas.common import ErrorResponse
from schemas.match_result import MatchRequest, MatchResultResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/match", tags=["Matching"])


@router.post(
    "",
    response_model=MatchResultResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or empty resume / job description payloads"},
        502: {"model": ErrorResponse, "description": "Upstream AI matching error"},
    },
    summary="Match Resume against Job Description",
    description="Compares structured candidate resume data against job requirements using Agent 3 (Resume Matcher).",
)
def match_resume_endpoint(request: MatchRequest) -> MatchResultResponse:
    if not request.resume or not isinstance(request.resume, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid non-empty resume payload is required.",
        )
    if not request.job_description or not isinstance(request.job_description, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid non-empty job_description payload is required.",
        )

    try:
        match_result = match_resume(request.resume, request.job_description)
    except ValueError as exc:
        logger.error("Agent 3 failed to match resume: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI matching service returned an invalid response structure.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 3: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error during candidate evaluation.",
        ) from exc

    return MatchResultResponse.model_validate(match_result)

