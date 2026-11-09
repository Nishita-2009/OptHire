"""
Repository layer providing data access functions for OptHire entities.
Follows SQLAlchemy 2.x standards with clean session handling and atomic operations.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    Candidate,
    Job,
    AnalysisRun,
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    HiringReport,
    now_utc,
)


# ==========================================
# CANDIDATE REPOSITORY
# ==========================================

def create_candidate(
    db: Session,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    resume_text: Optional[str] = None,
    parsed_resume_data: Optional[Dict[str, Any]] = None,
) -> Candidate:
    """Create and persist a new candidate profile."""
    candidate = Candidate(
        full_name=full_name,
        email=email,
        phone=phone,
        resume_text=resume_text,
        parsed_resume_data=parsed_resume_data,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def get_candidate(db: Session, candidate_id: str) -> Optional[Candidate]:
    """Retrieve a candidate by UUID."""
    stmt = select(Candidate).where(Candidate.id == candidate_id)
    return db.scalars(stmt).first()


def list_candidates(db: Session, skip: int = 0, limit: int = 100) -> List[Candidate]:
    """List candidates with pagination ordered by creation date descending."""
    stmt = select(Candidate).order_by(Candidate.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


# ==========================================
# JOB REPOSITORY
# ==========================================

def create_job(
    db: Session,
    title: str,
    description: str,
    company: Optional[str] = None,
    parsed_job_data: Optional[Dict[str, Any]] = None,
) -> Job:
    """Create and persist a new job posting."""
    job = Job(
        title=title,
        company=company,
        description=description,
        parsed_job_data=parsed_job_data,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Optional[Job]:
    """Retrieve a job by UUID."""
    stmt = select(Job).where(Job.id == job_id)
    return db.scalars(stmt).first()


def list_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
    """List job postings with pagination ordered by creation date descending."""
    stmt = select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


# ==========================================
# ANALYSIS RUN REPOSITORY
# ==========================================

def create_analysis_run(
    db: Session,
    candidate_id: str,
    job_id: str,
    status: str = "pending",
    resume_parse_result: Optional[Dict[str, Any]] = None,
    job_parse_result: Optional[Dict[str, Any]] = None,
    match_result: Optional[Dict[str, Any]] = None,
    skill_gap_result: Optional[Dict[str, Any]] = None,
    pipeline_error: Optional[str] = None,
) -> AnalysisRun:
    """Create a record representing an analysis run across Agents 1–5."""
    analysis = AnalysisRun(
        candidate_id=candidate_id,
        job_id=job_id,
        status=status,
        resume_parse_result=resume_parse_result,
        job_parse_result=job_parse_result,
        match_result=match_result,
        skill_gap_result=skill_gap_result,
        pipeline_error=pipeline_error,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis_run(db: Session, analysis_id: str) -> Optional[AnalysisRun]:
    """Retrieve an analysis run by UUID."""
    stmt = select(AnalysisRun).where(AnalysisRun.id == analysis_id)
    return db.scalars(stmt).first()


def list_candidate_analyses(
    db: Session, candidate_id: str, skip: int = 0, limit: int = 100
) -> List[AnalysisRun]:
    """List all analysis runs for a given candidate."""
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.candidate_id == candidate_id)
        .order_by(AnalysisRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def update_analysis_status(
    db: Session,
    analysis_id: str,
    status: str,
    resume_parse_result: Optional[Dict[str, Any]] = None,
    job_parse_result: Optional[Dict[str, Any]] = None,
    match_result: Optional[Dict[str, Any]] = None,
    skill_gap_result: Optional[Dict[str, Any]] = None,
    pipeline_error: Optional[str] = None,
) -> Optional[AnalysisRun]:
    """Update an analysis run with completed data or error status."""
    analysis = get_analysis_run(db, analysis_id)
    if not analysis:
        return None

    analysis.status = status
    if resume_parse_result is not None:
        analysis.resume_parse_result = resume_parse_result
    if job_parse_result is not None:
        analysis.job_parse_result = job_parse_result
    if match_result is not None:
        analysis.match_result = match_result
    if skill_gap_result is not None:
        analysis.skill_gap_result = skill_gap_result
    if pipeline_error is not None:
        analysis.pipeline_error = pipeline_error

    if status in ("completed", "failed"):
        analysis.completed_at = now_utc()

    db.commit()
    db.refresh(analysis)
    return analysis


# ==========================================
# INTERVIEW SESSION REPOSITORY
# ==========================================

def create_interview_session(
    db: Session,
    candidate_id: str,
    job_id: str,
    total_questions: int = 0,
    analysis_run_id: Optional[str] = None,
    status: str = "pending",
) -> InterviewSession:
    """Create a new interview session."""
    session = InterviewSession(
        candidate_id=candidate_id,
        job_id=job_id,
        analysis_run_id=analysis_run_id,
        status=status,
        total_questions=total_questions,
        current_question_index=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_interview_session(db: Session, session_id: str) -> Optional[InterviewSession]:
    """Retrieve an interview session by UUID."""
    stmt = select(InterviewSession).where(InterviewSession.id == session_id)
    return db.scalars(stmt).first()


def list_interview_sessions(
    db: Session,
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[InterviewSession]:
    """List interview sessions with optional candidate/job filters."""
    stmt = select(InterviewSession).order_by(InterviewSession.created_at.desc())
    if candidate_id:
        stmt = stmt.where(InterviewSession.candidate_id == candidate_id)
    if job_id:
        stmt = stmt.where(InterviewSession.job_id == job_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_interview_session_progress(
    db: Session,
    session_id: str,
    current_question_index: int,
    status: Optional[str] = None,
) -> Optional[InterviewSession]:
    """Update current question progress index and optionally session status."""
    session = get_interview_session(db, session_id)
    if not session:
        return None

    session.current_question_index = current_question_index
    if status:
        session.status = status
    if status == "in_progress" and not session.started_at:
        session.started_at = now_utc()

    db.commit()
    db.refresh(session)
    return session


def complete_interview_session(
    db: Session,
    session_id: str,
    final_summary: Dict[str, Any],
) -> Optional[InterviewSession]:
    """Mark an interview session as completed with final summary data."""
    session = get_interview_session(db, session_id)
    if not session:
        return None

    session.status = "completed"
    session.completed_at = now_utc()
    session.final_summary = final_summary
    session.current_question_index = session.total_questions

    db.commit()
    db.refresh(session)
    return session


# ==========================================
# INTERVIEW QUESTION REPOSITORY
# ==========================================

def add_interview_questions(
    db: Session,
    session_id: str,
    questions_data: List[Dict[str, Any]],
) -> List[InterviewQuestion]:
    """
    Bulk insert generated interview questions for a session.
    Updates the session's total_questions count atomically.
    """
    session = get_interview_session(db, session_id)
    if not session:
        raise ValueError(f"Interview session {session_id} not found.")

    created_questions = []
    for idx, q_data in enumerate(questions_data, start=1):
        q = InterviewQuestion(
            interview_session_id=session_id,
            question_identifier=q_data.get("id") or q_data.get("question_identifier") or f"Q_{idx:02d}",
            question_text=q_data.get("question") or q_data.get("question_text", ""),
            category=q_data.get("category", "General"),
            difficulty=q_data.get("difficulty", "medium"),
            purpose=q_data.get("purpose"),
            expected_points=q_data.get("expected_points") or q_data.get("expected_answer_points"),
            evaluation_criteria=q_data.get("evaluation_criteria"),
            sequence_number=idx,
        )
        db.add(q)
        created_questions.append(q)

    session.total_questions = len(created_questions)
    if session.status == "pending" and created_questions:
        session.status = "in_progress"
        session.started_at = now_utc()

    db.commit()
    for q in created_questions:
        db.refresh(q)
    db.refresh(session)
    return created_questions


def get_interview_questions(db: Session, session_id: str) -> List[InterviewQuestion]:
    """Get all questions for a session ordered by sequence number."""
    stmt = (
        select(InterviewQuestion)
        .where(InterviewQuestion.interview_session_id == session_id)
        .order_by(InterviewQuestion.sequence_number.asc())
    )
    return list(db.scalars(stmt).all())


def get_interview_question(db: Session, question_id: str) -> Optional[InterviewQuestion]:
    """Retrieve an interview question by UUID."""
    stmt = select(InterviewQuestion).where(InterviewQuestion.id == question_id)
    return db.scalars(stmt).first()


def get_interview_question_by_sequence(
    db: Session, session_id: str, sequence_number: int
) -> Optional[InterviewQuestion]:
    """Retrieve an interview question by session and 1-based sequence number."""
    stmt = (
        select(InterviewQuestion)
        .where(
            InterviewQuestion.interview_session_id == session_id,
            InterviewQuestion.sequence_number == sequence_number,
        )
    )
    return db.scalars(stmt).first()


# ==========================================
# INTERVIEW ANSWER REPOSITORY
# ==========================================

def save_interview_answer(
    db: Session,
    question_id: str,
    answer_text: str,
    evaluation_result: Optional[Dict[str, Any]] = None,
    score: Optional[float] = None,
) -> InterviewAnswer:
    """
    Persist an answer for an interview question with optional evaluation.
    Enforces that each question can only have one answer.
    """
    stmt = select(InterviewAnswer).where(InterviewAnswer.interview_question_id == question_id)
    existing = db.scalars(stmt).first()
    if existing:
        raise ValueError(f"Question {question_id} has already been answered.")

    answer = InterviewAnswer(
        interview_question_id=question_id,
        answer_text=answer_text,
        evaluation_result=evaluation_result,
        score=score,
        evaluated_at=now_utc() if evaluation_result is not None else None,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def get_answer_for_question(db: Session, question_id: str) -> Optional[InterviewAnswer]:
    """Retrieve answer submitted for a specific question."""
    stmt = select(InterviewAnswer).where(InterviewAnswer.interview_question_id == question_id)
    return db.scalars(stmt).first()


def get_interview_answers(db: Session, session_id: str) -> List[InterviewAnswer]:
    """Retrieve all submitted answers for a given interview session."""
    stmt = (
        select(InterviewAnswer)
        .join(InterviewQuestion, InterviewAnswer.interview_question_id == InterviewQuestion.id)
        .where(InterviewQuestion.interview_session_id == session_id)
        .order_by(InterviewQuestion.sequence_number.asc())
    )
    return list(db.scalars(stmt).all())


# ==========================================
# HIRING REPORT REPOSITORY
# ==========================================

def create_hiring_report(
    db: Session,
    analysis_run_id: str,
    report_data: Dict[str, Any],
    recommendation: str,
    overall_score: Optional[float] = None,
    interview_session_id: Optional[str] = None,
) -> HiringReport:
    """Create and persist a final hiring report."""
    report = HiringReport(
        analysis_run_id=analysis_run_id,
        interview_session_id=interview_session_id,
        report_data=report_data,
        recommendation=recommendation,
        overall_score=overall_score,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_hiring_report(db: Session, report_id: str) -> Optional[HiringReport]:
    """Retrieve a hiring report by UUID."""
    stmt = select(HiringReport).where(HiringReport.id == report_id)
    return db.scalars(stmt).first()


def get_report_by_analysis_id(db: Session, analysis_run_id: str) -> Optional[HiringReport]:
    """Retrieve the hiring report linked to a specific analysis run."""
    stmt = select(HiringReport).where(HiringReport.analysis_run_id == analysis_run_id)
    return db.scalars(stmt).first()

