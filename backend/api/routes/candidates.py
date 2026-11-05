"""
Candidate Management API Endpoints.
Provides persistent CRUD and analysis history for candidate profiles.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.db import get_db
from database import repository
from schemas.common import ErrorResponse
from schemas.entities import (
    CandidateCreate,
    CandidateResponse,
    CandidateListResponse,
    AnalysisRunResponse,
    AnalysisRunListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid candidate payload"},
    },
    summary="Create Candidate Profile",
    description="Registers a new candidate profile with optional parsed resume data in the persistent database.",
)
def create_candidate_endpoint(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
) -> CandidateResponse:
    try:
        candidate = repository.create_candidate(
            db=db,
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            resume_text=payload.resume_text,
            parsed_resume_data=payload.parsed_resume_data,
        )
        return CandidateResponse.model_validate(candidate)
    except Exception as exc:
        logger.error("Failed to create candidate: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate: {str(exc)}",
        ) from exc


@router.get(
    "",
    response_model=CandidateListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Candidates",
    description="Retrieves a paginated list of registered candidates.",
)
def list_candidates_endpoint(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Limit for pagination"),
    db: Session = Depends(get_db),
) -> CandidateListResponse:
    candidates = repository.list_candidates(db, skip=skip, limit=limit)
    return CandidateListResponse(
        total=len(candidates),
        candidates=[CandidateResponse.model_validate(c) for c in candidates],
    )


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Candidate not found"},
    },
    summary="Get Candidate Details",
    description="Retrieves candidate profile and parsed resume by candidate UUID.",
)
def get_candidate_endpoint(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateResponse:
    candidate = repository.get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{candidate_id}' not found.",
        )
    return CandidateResponse.model_validate(candidate)


@router.get(
    "/{candidate_id}/analysis",
    response_model=AnalysisRunListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Candidate not found"},
    },
    summary="List Candidate Analysis Runs",
    description="Retrieves all analysis runs performed for a specific candidate.",
)
def get_candidate_analyses_endpoint(
    candidate_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> AnalysisRunListResponse:
    candidate = repository.get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{candidate_id}' not found.",
        )
    runs = repository.list_candidate_analyses(db, candidate_id=candidate_id, skip=skip, limit=limit)
    return AnalysisRunListResponse(
        total=len(runs),
        runs=[AnalysisRunResponse.model_validate(r) for r in runs],
    )
