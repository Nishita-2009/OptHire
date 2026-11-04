"""
Interview Generation (Agent 5) and Answer Evaluation (Agent 6) Endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status

from agents.interview_generator.parser import generate_interview
from agents.interview_evaluator.evaluator import evaluate_answer
from schemas.common import ErrorResponse
from schemas.interview import (
    AnswerEvaluationRequest,
    AnswerEvaluationResponse,
    InterviewGenerateRequest,
    InterviewGenerationResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interview", tags=["Interviews"])


@router.post(
    "/generate",
    response_model=InterviewGenerationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input structures"},
        502: {"model": ErrorResponse, "description": "Upstream AI generation or validation error"},
    },
    summary="Generate 21 Personalized Interview Questions",
    description="Generates a validated 21-question interview across 7 categories using Agent 5 (Interview Generator).",
)
def generate_interview_endpoint(
    request: InterviewGenerateRequest,
) -> InterviewGenerationResponse:
    if not request.resume or not request.job_description or not request.match_result or not request.skill_gap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume, job description, match result, and skill gap payloads are all required.",
        )

    try:
        interview = generate_interview(
            resume=request.resume,
            job_description=request.job_description,
            match_result=request.match_result,
            skill_gap=request.skill_gap,
        )
    except ValueError as exc:
        logger.error("Agent 5 validation/generation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Interview question generation failed validation: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 5: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error while generating interview questions.",
        ) from exc

    return InterviewGenerationResponse.model_validate(interview)


@router.post(
    "/evaluate",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Missing question rubric or candidate answer"},
        502: {"model": ErrorResponse, "description": "Upstream AI evaluation error"},
    },
    summary="Evaluate Single Candidate Interview Answer",
    description="Evaluates an individual interview answer against its question rubric using Agent 6 (Interview Evaluator). Does not manage state or aggregate full sessions.",
)
def evaluate_answer_endpoint(
    request: AnswerEvaluationRequest,
) -> AnswerEvaluationResponse:
    if not request.question or not isinstance(request.question, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid question rubric dictionary is required.",
        )
    clean_answer = request.candidate_answer.strip()
    if not clean_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate answer cannot be empty or purely whitespace.",
        )

    try:
        evaluation = evaluate_answer(
            question=request.question,
            candidate_answer=clean_answer,
        )
    except ValueError as exc:
        logger.error("Agent 6 failed to evaluate answer: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI answer evaluation returned an invalid response structure.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error in Agent 6: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service encountered an unexpected error while evaluating candidate answer.",
        ) from exc

    return AnswerEvaluationResponse.model_validate(evaluation)
