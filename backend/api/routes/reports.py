"""
Hiring Report Generation Endpoint (Agent 7).
"""
import logging
from fastapi import APIRouter, HTTPException, status

from agents.hiring_report.generator import generate_hiring_report
from schemas.common import ErrorResponse
from schemas.report import HiringReportRequest, HiringReportResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Hiring Reports"])


@router.post(
    "/generate",
    response_model=HiringReportResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Missing required candidate journey components"},
        502: {"model": ErrorResponse, "description": "Upstream AI report generation error"},
    },
    summary="Generate Final Executive Hiring Report",
    description="Synthesizes resume parsing, ATS matching, skill gap analysis, and interview evaluations into a holistic executive hiring report with decision-support disclaimers using Agent 7.",
)
def generate_report_endpoint(
    request: HiringReportRequest,
) -> HiringReportResponse:
    if (
        not request.resume
        or not request.job_description
        or not request.match_result
        or not request.skill_gap
        or not request.interview_summary
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume, job description, match result, skill gap, and interview summary are all required.",
        )

    try:
        report = generate_hiring_report(
            resume=request.resume,
            job_description=request.job_description,
            match_result=request.match_result,
            skill_gap=request.skill_gap,
            interview_summary=request.interview_summary,
        )
    except ValueError as exc:
        logger.error("Agent 7 validation/generation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hiring report generation failed validation: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 7: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error while generating the hiring report.",
        ) from exc

    return HiringReportResponse.model_validate(report)
