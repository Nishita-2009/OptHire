"""
Hiring Pipeline Orchestration Endpoint (Agents 1–5).
"""
import logging
import os
import shutil
import tempfile
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from orchestrator.hiring_pipeline import HiringPipeline
from schemas.common import ErrorResponse
from schemas.pipeline import PipelineResponse
from services.file_service import save_upload_to_temp_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post(
    "/run",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file upload or empty job description"},
        413: {"model": ErrorResponse, "description": "File size exceeds limit"},
        415: {"model": ErrorResponse, "description": "Unsupported media type (non-PDF)"},
        502: {"model": ErrorResponse, "description": "Upstream AI error during pipeline execution"},
    },
    summary="Execute Full Analysis Pipeline (Agents 1–5)",
    description="Sequentially executes Resume Parser (1), JD Parser (2), Matcher (3), Skill Gap Analyzer (4), and Interview Generator (5) using the existing HiringPipeline.",
)
def run_pipeline_endpoint(
    file: UploadFile = File(..., description="Candidate resume PDF document"),
    job_description: str = Form(..., description="Target job description text"),
) -> PipelineResponse:
    cleaned_jd = job_description.strip()
    if not cleaned_jd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty or purely whitespace.",
        )

    # Isolated temporary output directory for this request to prevent disk bloat
    temp_output_dir = tempfile.mkdtemp(prefix="opthire_pipeline_")

    try:
        with save_upload_to_temp_file(file) as temp_pdf_path:
            pipeline = HiringPipeline(output_directory=temp_output_dir)
            result = pipeline.run(
                resume_path=temp_pdf_path,
                job_description=cleaned_jd,
            )
    except HTTPException:
        raise
    except ValueError as exc:
        logger.error("HiringPipeline validation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hiring pipeline failed during agent execution: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in HiringPipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error during pipeline orchestration.",
        ) from exc
    finally:
        # Guarantee removal of ephemeral output artifacts from this run
        if os.path.exists(temp_output_dir):
            shutil.rmtree(temp_output_dir, ignore_errors=True)

    return PipelineResponse.model_validate(result)
