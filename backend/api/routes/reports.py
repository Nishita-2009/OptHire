"""
Hiring Report Generation (Agent 7) and Persistent Report Endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from agents.hiring_report.generator import generate_hiring_report
from database.db import get_db
from database import repository
from services.interview_service import InterviewService
from schemas.common import ErrorResponse
from schemas.report import HiringReportRequest, HiringReportResponse
from schemas.entities import (
    GenerateHiringReportEntityRequest,
    HiringReportEntityResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Hiring Reports"])


# ==========================================
# 1. STATELESS REPORT GENERATION (PHASE 2)
# ==========================================

@router.post(
    "/generate",
    response_model=HiringReportResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Missing required candidate journey components"},
        502: {"model": ErrorResponse, "description": "Upstream AI report generation error"},
    },
    summary="Generate Final Executive Hiring Report (Stateless)",
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
        req_title = request.job_description.get("job_title") or request.job_description.get("title")
        req_name = request.resume.get("name") or request.resume.get("candidate_name")
        req_company = request.job_description.get("company")
        if req_title or req_name:
            report = InterviewService.harmonize_report_narratives(
                report=report,
                candidate_name=req_name,
                job_title=req_title,
                company=req_company,
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


# ==========================================
# 2. PERSISTENT HIRING REPORT ENDPOINTS
# ==========================================

@router.post(
    "",
    response_model=HiringReportEntityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Missing prerequisite analysis or invalid state"},
        404: {"model": ErrorResponse, "description": "Analysis run or session not found"},
        502: {"model": ErrorResponse, "description": "AI report generation error"},
    },
    summary="Generate and Persist Final Hiring Report",
    description="Synthesizes candidate analysis and interview results via Agent 7 and saves report to database.",
)
def create_persistent_report_endpoint(
    payload: GenerateHiringReportEntityRequest,
    db: Session = Depends(get_db),
) -> HiringReportEntityResponse:
    try:
        result = InterviewService.generate_and_save_hiring_report(
            db=db,
            analysis_run_id=payload.analysis_run_id,
            interview_session_id=payload.interview_session_id,
        )
        return HiringReportEntityResponse(**result)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
    except Exception as exc:
        logger.error("Failed to generate persistent hiring report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Report generation failed: {str(exc)}",
        ) from exc


@router.get(
    "/{report_id}",
    response_model=HiringReportEntityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
    summary="Get Persisted Hiring Report",
    description="Retrieves a persisted executive hiring report by report UUID.",
)
def get_persistent_report_endpoint(
    report_id: str,
    db: Session = Depends(get_db),
) -> HiringReportEntityResponse:
    report = repository.get_hiring_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hiring report with ID '{report_id}' not found.",
        )
    return HiringReportEntityResponse.model_validate(report)
