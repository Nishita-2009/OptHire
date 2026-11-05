"""
Job Description Parsing (Agent 2) and Job Entity Management Endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from agents.jd_parser.parser import parse_job_description
from database.db import get_db
from database import repository
from schemas.common import ErrorResponse
from schemas.job_description import JobDescriptionParsedResponse, JobDescriptionRequest
from schemas.entities import JobCreate, JobEntityResponse, JobEntityListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs & Descriptions"])


# ==========================================
# 1. PARSE JOB DESCRIPTION (AGENT 2)
# ==========================================

@router.post(
    "/parse",
    response_model=JobDescriptionParsedResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or empty job description text"},
        502: {"model": ErrorResponse, "description": "Upstream AI parsing error"},
    },
    summary="Parse Job Description Text",
    description="Extracts structured job requirements and qualifications using Agent 2 (JD Parser).",
)
def parse_job_endpoint(request: JobDescriptionRequest) -> JobDescriptionParsedResponse:
    cleaned_jd = request.job_description.strip()
    if not cleaned_jd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty or purely whitespace.",
        )

    try:
        parsed_result = parse_job_description(cleaned_jd)
    except ValueError as exc:
        logger.error("Agent 2 failed to parse job description: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to extract structured requirements from job description.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 2: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error while parsing the job description.",
        ) from exc

    return JobDescriptionParsedResponse.model_validate(parsed_result)


# ==========================================
# 2. PERSISTENT JOB ENTITY CRUD
# ==========================================

@router.post(
    "",
    response_model=JobEntityResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid job payload"},
    },
    summary="Create Job Posting",
    description="Creates a new job posting with raw text and optional parsed structured requirements.",
)
def create_job_endpoint(
    payload: JobCreate,
    db: Session = Depends(get_db),
) -> JobEntityResponse:
    try:
        job = repository.create_job(
            db=db,
            title=payload.title,
            company=payload.company,
            description=payload.description,
            parsed_job_data=payload.parsed_job_data,
        )
        return JobEntityResponse.model_validate(job)
    except Exception as exc:
        logger.error("Failed to create job entity: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(exc)}",
        ) from exc


@router.get(
    "",
    response_model=JobEntityListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Job Postings",
    description="Retrieves a paginated list of job openings registered in the database.",
)
def list_jobs_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> JobEntityListResponse:
    jobs = repository.list_jobs(db, skip=skip, limit=limit)
    return JobEntityListResponse(
        total=len(jobs),
        jobs=[JobEntityResponse.model_validate(j) for j in jobs],
    )


@router.get(
    "/{job_id}",
    response_model=JobEntityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
    summary="Get Job Details",
    description="Retrieves job posting details and structured requirements by job UUID.",
)
def get_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobEntityResponse:
    job = repository.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return JobEntityResponse.model_validate(job)
