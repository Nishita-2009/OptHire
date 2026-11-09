"""
Persistent Interview Sessions Endpoints.
Coordinates stateful candidate interview sessions with Agent 5 (generation) and Agent 6 (evaluation).
"""
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.db import get_db
from database import repository
from services.interview_service import InterviewService
from schemas.common import ErrorResponse
from schemas.entities import (
    InterviewSessionCreate,
    InterviewSessionDetailResponse,
    InterviewQuestionItem,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    CompleteInterviewResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interviews", tags=["Persistent Interview Sessions"])


@router.post(
    "",
    response_model=InterviewSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid session parameters or missing data"},
        404: {"model": ErrorResponse, "description": "Candidate or Job not found"},
        502: {"model": ErrorResponse, "description": "Upstream AI generation error"},
    },
    summary="Initialize Interview Session",
    description="Creates a persistent interview session. Automatically generates 21 questions across 7 categories via Agent 5 if candidate and job data are available.",
)
def create_interview_session_endpoint(
    payload: InterviewSessionCreate,
    db: Session = Depends(get_db),
) -> InterviewSessionDetailResponse:
    try:
        session = InterviewService.create_session(
            db=db,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            analysis_run_id=payload.analysis_run_id,
            generate_questions=payload.generate_questions,
            custom_questions=payload.custom_questions,
        )
        details = InterviewService.get_session_details(db, session.id)
        return InterviewSessionDetailResponse(**details)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
    except Exception as exc:
        logger.error("Failed to create interview session: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Interview session initialization failed: {str(exc)}",
        ) from exc


@router.get(
    "/{session_id}",
    response_model=InterviewSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Interview session not found"},
    },
    summary="Get Interview Session Details",
    description="Retrieves current session state, progress, active question, and questions with answer statuses.",
)
def get_interview_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
) -> InterviewSessionDetailResponse:
    try:
        details = InterviewService.get_session_details(db, session_id)
        return InterviewSessionDetailResponse(**details)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{session_id}/questions",
    response_model=List[InterviewQuestionItem],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Interview session not found"},
    },
    summary="List Interview Session Questions",
    description="Lists all ordered questions generated for an interview session.",
)
def get_session_questions_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
) -> List[InterviewQuestionItem]:
    session = repository.get_interview_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session with ID '{session_id}' not found.",
        )
    questions = repository.get_interview_questions(db, session_id)
    answers = repository.get_interview_answers(db, session_id)
    answer_map = {ans.interview_question_id: ans for ans in answers}

    items = []
    for q in questions:
        ans = answer_map.get(q.id)
        items.append(
            InterviewQuestionItem(
                id=q.id,
                sequence_number=q.sequence_number,
                question_identifier=q.question_identifier,
                question_text=q.question_text,
                category=q.category,
                difficulty=q.difficulty,
                purpose=q.purpose,
                expected_points=q.expected_points,
                evaluation_criteria=q.evaluation_criteria,
                is_answered=ans is not None,
                answer_text=ans.answer_text if ans else None,
                score=ans.score if ans else None,
                evaluation_result=ans.evaluation_result if ans else None,
            )
        )
    return items


@router.post(
    "/{session_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Question already answered or session completed"},
        404: {"model": ErrorResponse, "description": "Session or Question not found"},
        502: {"model": ErrorResponse, "description": "Upstream AI evaluation error"},
    },
    summary="Submit and Evaluate Candidate Answer",
    description="Submits an answer for an interview question, runs Agent 6 evaluation, saves evaluation rubric, and updates session progress.",
)
def submit_answer_endpoint(
    session_id: str,
    payload: SubmitAnswerRequest,
    db: Session = Depends(get_db),
) -> SubmitAnswerResponse:
    try:
        result = InterviewService.submit_and_evaluate_answer(
            db=db,
            session_id=session_id,
            question_id=payload.question_id,
            answer_text=payload.answer,
        )
        return SubmitAnswerResponse(**result)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
    except Exception as exc:
        logger.error("Failed to submit and evaluate answer: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Answer evaluation failed: {str(exc)}",
        ) from exc


@router.get(
    "/{session_id}/answers",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Interview session not found"},
    },
    summary="List Submitted Answers",
    description="Lists all submitted answers and Agent 6 evaluation scores for an interview session.",
)
def get_session_answers_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    session = repository.get_interview_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session with ID '{session_id}' not found.",
        )
    answers = repository.get_interview_answers(db, session_id)
    return [
        {
            "id": ans.id,
            "interview_question_id": ans.interview_question_id,
            "answer_text": ans.answer_text,
            "score": ans.score,
            "evaluation_result": ans.evaluation_result,
            "submitted_at": ans.submitted_at,
            "evaluated_at": ans.evaluated_at,
        }
        for ans in answers
    ]


@router.post(
    "/{session_id}/complete",
    response_model=CompleteInterviewResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "No answers submitted or invalid session state"},
        404: {"model": ErrorResponse, "description": "Interview session not found"},
        502: {"model": ErrorResponse, "description": "AI summary generation error"},
    },
    summary="Complete Interview Session",
    description="Explicitly completes an interview session, triggering Agent 6 to generate a final interview summary across all answers.",
)
def complete_interview_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
) -> CompleteInterviewResponse:
    try:
        session = InterviewService.finalize_interview_session(db, session_id)
        answers = repository.get_interview_answers(db, session_id)
        return CompleteInterviewResponse(
            session_id=session.id,
            status=session.status,
            total_questions=session.total_questions,
            answered_count=len(answers),
            final_summary=session.final_summary,
            completed_at=session.completed_at,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc
    except Exception as exc:
        logger.error("Failed to complete interview session: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Interview completion failed: {str(exc)}",
        ) from exc

