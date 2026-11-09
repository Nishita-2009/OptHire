"""
SQLAlchemy ORM models for OptHire persistent database layer.
Normalized entities supporting candidates, job postings, analysis runs,
interview sessions with questions/answers, and final hiring reports.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.db import Base


def generate_uuid() -> str:
    """Generates a UUID4 string representation."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class Candidate(Base):
    """
    Candidate entity representing an applicant with parsed profile details.
    """
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    resume_text = Column(Text, nullable=True)
    parsed_resume_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationships
    analysis_runs = relationship("AnalysisRun", back_populates="candidate", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="candidate", cascade="all, delete-orphan")


class Job(Base):
    """
    Job entity representing a job description / role opening.
    """
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=False)
    parsed_job_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationships
    analysis_runs = relationship("AnalysisRun", back_populates="job", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="job", cascade="all, delete-orphan")


class AnalysisRun(Base):
    """
    Represents one execution of the hiring analysis pipeline (Agents 1–5).
    """
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, completed, failed
    resume_parse_result = Column(JSON, nullable=True)
    job_parse_result = Column(JSON, nullable=True)
    match_result = Column(JSON, nullable=True)
    skill_gap_result = Column(JSON, nullable=True)
    pipeline_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="analysis_runs")
    job = relationship("Job", back_populates="analysis_runs")
    interview_sessions = relationship("InterviewSession", back_populates="analysis_run")
    hiring_report = relationship("HiringReport", back_populates="analysis_run", uselist=False, cascade="all, delete-orphan")


class InterviewSession(Base):
    """
    Persistent stateful interview session for a candidate applying to a job.
    """
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, in_progress, completed, cancelled
    current_question_index = Column(Integer, default=0, nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    final_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="interview_sessions")
    job = relationship("Job", back_populates="interview_sessions")
    analysis_run = relationship("AnalysisRun", back_populates="interview_sessions")
    questions = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.sequence_number",
    )
    hiring_reports = relationship("HiringReport", back_populates="interview_session")


class InterviewQuestion(Base):
    """
    Individual question within an interview session, populated from Agent 5.
    """
    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_identifier = Column(String(50), nullable=False, index=True)  # e.g. TECH_01, CODE_01
    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False)
    purpose = Column(Text, nullable=True)
    expected_points = Column(JSON, nullable=True)
    evaluation_criteria = Column(JSON, nullable=True)
    sequence_number = Column(Integer, nullable=False, index=True)

    # Relationships
    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class InterviewAnswer(Base):
    """
    Candidate's submitted answer and Agent 6 evaluation for a specific interview question.
    """
    __tablename__ = "interview_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_question_id = Column(
        String(36),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    answer_text = Column(Text, nullable=False)
    evaluation_result = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    question = relationship("InterviewQuestion", back_populates="answer")


class HiringReport(Base):
    """
    Comprehensive synthesized hiring report (Agent 7) linked to an analysis run.
    """
    __tablename__ = "hiring_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    report_data = Column(JSON, nullable=False)
    recommendation = Column(String(50), nullable=False, index=True)
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="hiring_report")
    interview_session = relationship("InterviewSession", back_populates="hiring_reports")

    @property
    def is_provisional(self) -> bool:
        """Indicates whether this report is provisional due to an incomplete interview session."""
        if isinstance(self.report_data, dict):
            return bool(self.report_data.get("is_provisional", False))
        return False


