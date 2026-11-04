"""
Resume Parsing Endpoint (Agent 1).
"""
import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from agents.resume_parser.parser import parse_resume
from schemas.common import ErrorResponse
from schemas.resume import ResumeParsedResponse
from services.file_service import extract_text_from_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "/parse",
    response_model=ResumeParsedResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file upload or empty file"},
        413: {"model": ErrorResponse, "description": "File size exceeds limit"},
        415: {"model": ErrorResponse, "description": "Unsupported media type (non-PDF)"},
        422: {"model": ErrorResponse, "description": "Unable to extract text from PDF"},
        502: {"model": ErrorResponse, "description": "Upstream AI parsing error"},
    },
    summary="Parse Candidate Resume PDF",
    description="Extracts candidate information from an uploaded PDF resume using Agent 1 (Resume Parser).",
)
def parse_resume_endpoint(
    file: UploadFile = File(..., description="Candidate resume PDF file"),
) -> ResumeParsedResponse:
    # Validate and extract text safely with guaranteed temp file removal
    resume_text = extract_text_from_upload(file)

    try:
        parsed_result = parse_resume(resume_text)
    except ValueError as exc:
        logger.error("Agent 1 failed to parse resume JSON: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to extract structured data from resume. Upstream AI returned an invalid response.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 1: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error while processing the resume.",
        ) from exc

    return ResumeParsedResponse.model_validate(parsed_result)
