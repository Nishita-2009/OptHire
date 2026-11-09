"""
Analysis Run Endpoints.
Executes and tracks persistent candidate evaluation pipelines (Agents 1–4).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.db import get_db
from database import repository
from agents.resume_matcher.parser import match_resume
from agents.skill_gap.parser import analyze_skill_gap
from agents.jd_parser.parser import parse_job_description
from schemas.common import ErrorResponse
from schemas.entities import (
    AnalysisRunCreate,
    AnalysisRunResponse,
    HiringReportEntityResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Candidate Analysis"])


@router.post(
    "",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Candidate or Job not found or invalid"},
        502: {"model": ErrorResponse, "description": "AI analysis processing error"},
    },
    summary="Trigger or Record Analysis Run",
    description="Executes candidate vs job matching (Agent 3) and skill gap analysis (Agent 4) and persists the run.",
)
def create_analysis_endpoint(
    payload: AnalysisRunCreate,
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    candidate = repository.get_candidate(db, payload.candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{payload.candidate_id}' not found.",
        )

    job = repository.get_job(db, payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{payload.job_id}' not found.",
        )

    # Initialize analysis run
    analysis = repository.create_analysis_run(
        db=db,
        candidate_id=candidate.id,
        job_id=job.id,
        status="pending",
    )

    resume_data = dict(candidate.parsed_resume_data or {})
    if candidate.full_name:
        resume_data["name"] = candidate.full_name
        resume_data["candidate_name"] = candidate.full_name

    job_data = dict(job.parsed_job_data or {})
    if job.title:
        job_data["job_title"] = job.title
        job_data["title"] = job.title
    if job.company:
        job_data["company"] = job.company

    # Parse JD if not already parsed
    if not job.parsed_job_data and job.description:
        try:
            parsed_jd = parse_job_description(job.description)
            if job.title:
                parsed_jd["job_title"] = job.title
                parsed_jd["title"] = job.title
            if job.company:
                parsed_jd["company"] = job.company
            job.parsed_job_data = parsed_jd
            db.commit()
            for k, v in parsed_jd.items():
                job_data.setdefault(k, v)
            if job.title:
                job_data["job_title"] = job.title
                job_data["title"] = job.title
            if job.company:
                job_data["company"] = job.company
        except Exception as exc:
            logger.warning("Could not auto-parse job description for analysis %s: %s", analysis.id, exc)

    # Run Matcher (Agent 3) and Skill Gap (Agent 4) if data exists
    if resume_data and job_data:
        try:
            logger.info("Executing Agent 3 (Matcher) for analysis %s", analysis.id)
            match_res = match_resume(resume_data, job_data)

            logger.info("Executing Agent 4 (Skill Gap) for analysis %s", analysis.id)
            skill_res = analyze_skill_gap(resume_data, job_data, match_res)

            analysis = repository.update_analysis_status(
                db=db,
                analysis_id=analysis.id,
                status="completed",
                resume_parse_result=resume_data,
                job_parse_result=job_data,
                match_result=match_res,
                skill_gap_result=skill_res,
            )
        except Exception as exc:
            logger.error("Analysis execution failed for run %s: %s", analysis.id, exc)
            analysis = repository.update_analysis_status(
                db=db,
                analysis_id=analysis.id,
                status="failed",
                pipeline_error=str(exc),
            )
    else:
        # Mark completed with available data
        analysis = repository.update_analysis_status(
            db=db,
            analysis_id=analysis.id,
            status="completed",
            resume_parse_result=resume_data,
            job_parse_result=job_data,
        )

    return AnalysisRunResponse.model_validate(analysis)


@router.get(
    "/{analysis_id}",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Analysis run not found"},
    },
    summary="Get Analysis Run",
    description="Retrieves the full inputs and results of a candidate-job analysis run.",
)
def get_analysis_endpoint(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    analysis = repository.get_analysis_run(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis run with ID '{analysis_id}' not found.",
        )
    return AnalysisRunResponse.model_validate(analysis)


@router.get(
    "/{analysis_id}/report",
    response_model=HiringReportEntityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Hiring report not found for this analysis run"},
    },
    summary="Get Analysis Hiring Report",
    description="Retrieves the final executive hiring report associated with an analysis run.",
)
def get_analysis_report_endpoint(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> HiringReportEntityResponse:
    report = repository.get_report_by_analysis_id(db, analysis_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hiring report found for analysis run '{analysis_id}'.",
        )
    return HiringReportEntityResponse.model_validate(report)
