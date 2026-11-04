"""
Job Description Parsing Endpoint (Agent 2).
"""
import logging
from fastapi import APIRouter, HTTPException, status

from agents.jd_parser.parser import parse_job_description
from schemas.common import ErrorResponse
from schemas.job_description import JobDescriptionParsedResponse, JobDescriptionRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])


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
