"""
Pydantic v2 schemas for persistent database entities:
Candidates, Jobs, Analysis Runs, Persistent Interview Sessions, and Hiring Reports.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# CANDIDATE SCHEMAS
# ==========================================

class CandidateCreate(BaseModel):
    """Payload to create or persist a candidate profile."""
    full_name: Optional[str] = Field(None, max_length=255, description="Full name of candidate")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    resume_text: Optional[str] = Field(None, description="Extracted raw resume text")
    parsed_resume_data: Optional[Dict[str, Any]] = Field(None, description="Parsed JSON resume structure")


class CandidateResponse(BaseModel):
    """Candidate response entity representation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_text: Optional[str] = None
    parsed_resume_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CandidateListResponse(BaseModel):
    """Paginated or listed candidates response."""
    total: int
    candidates: List[CandidateResponse]


# ==========================================
# JOB SCHEMAS
# ==========================================

class JobCreate(BaseModel):
    """Payload to create or register a job opening."""
    title: str = Field(..., min_length=2, max_length=255, description="Job title")
    description: str = Field(..., min_length=10, description="Full job description text")
    company: Optional[str] = Field(None, max_length=255, description="Hiring company name")
    parsed_job_data: Optional[Dict[str, Any]] = Field(None, description="Structured parsed JD schema")


class JobEntityResponse(BaseModel):
    """Job response entity representation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    company: Optional[str] = None
    description: str
    parsed_job_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class JobEntityListResponse(BaseModel):
    """List of persisted job postings."""
    total: int
    jobs: List[JobEntityResponse]


# ==========================================
# ANALYSIS RUN SCHEMAS
# ==========================================

class AnalysisRunCreate(BaseModel):
    """Payload to trigger or record an analysis run between candidate and job."""
    candidate_id: str = Field(..., description="UUID of candidate")
    job_id: str = Field(..., description="UUID of job")


class AnalysisRunResponse(BaseModel):
    """Record of an analysis pipeline run."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    job_id: str
    status: str
    resume_parse_result: Optional[Dict[str, Any]] = None
    job_parse_result: Optional[Dict[str, Any]] = None
    match_result: Optional[Dict[str, Any]] = None
    skill_gap_result: Optional[Dict[str, Any]] = None
    pipeline_error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AnalysisRunListResponse(BaseModel):
    """List of analysis runs."""
    total: int
    runs: List[AnalysisRunResponse]


# ==========================================
# INTERVIEW SESSION SCHEMAS
# ==========================================

class InterviewSessionCreate(BaseModel):
    """Payload to initialize a persistent interview session."""
    candidate_id: str = Field(..., description="Candidate UUID")
    job_id: str = Field(..., description="Job UUID")
    analysis_run_id: Optional[str] = Field(None, description="Optional associated analysis run UUID")
    generate_questions: bool = Field(True, description="Whether to invoke Agent 5 to generate 21 questions")
    custom_questions: Optional[List[Dict[str, Any]]] = Field(None, description="Optional custom questions")


class InterviewQuestionItem(BaseModel):
    """Question item representation in an interview session."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence_number: int
    question_identifier: str
    question_text: str
    category: str
    difficulty: str
    purpose: Optional[str] = None
    expected_points: Optional[Any] = None
    evaluation_criteria: Optional[Any] = None
    is_answered: Optional[bool] = None
    answer_text: Optional[str] = None
    score: Optional[float] = None
    evaluation_result: Optional[Dict[str, Any]] = None


class InterviewSessionResponse(BaseModel):
    """Metadata response for an interview session."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    job_id: str
    analysis_run_id: Optional[str] = None
    status: str
    current_question_index: int
    total_questions: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class InterviewSessionDetailResponse(BaseModel):
    """Detailed state of an ongoing or completed interview session."""
    session_id: str
    candidate_id: str
    job_id: str
    analysis_run_id: Optional[str] = None
    status: str
    current_question_index: int
    total_questions: int
    answered_questions_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_summary: Optional[Dict[str, Any]] = None
    current_question: Optional[Dict[str, Any]] = None
    questions: List[InterviewQuestionItem]


class SubmitAnswerRequest(BaseModel):
    """Candidate answer submission."""
    question_id: str = Field(..., description="Interview question UUID")
    answer: str = Field(..., min_length=1, description="Candidate submitted answer text")


class SubmitAnswerResponse(BaseModel):
    """Response returned after evaluating candidate answer with Agent 6."""
    session_id: str
    question_id: str
    answer_id: str
    answer_text: str
    score: Optional[float] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    session_status: str
    current_question_index: int
    total_questions: int
    is_interview_completed: bool


class CompleteInterviewResponse(BaseModel):
    """Response after completing an interview session."""
    session_id: str
    status: str
    total_questions: int
    answered_count: int
    final_summary: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


# ==========================================
# HIRING REPORT ENTITY SCHEMAS
# ==========================================

class GenerateHiringReportEntityRequest(BaseModel):
    """Request to generate and persist a final hiring report."""
    analysis_run_id: str = Field(..., description="UUID of completed analysis run")
    interview_session_id: Optional[str] = Field(None, description="Optional interview session UUID")


class HiringReportEntityResponse(BaseModel):
    """Persisted hiring report response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_run_id: str
    interview_session_id: Optional[str] = None
    recommendation: str
    overall_score: Optional[float] = None
    is_provisional: Optional[bool] = False
    report_data: Dict[str, Any]
    created_at: datetime


