"""
Database Layer Tests for OptHire.
Tests engine creation, session management, all ORM models CRUD,
cascading deletes, unique constraints, and transaction rollbacks.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from database.models import (
    Candidate,
    Job,
    AnalysisRun,
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    HiringReport,
)
from database import repository


def test_candidate_crud(db_session):
    """Test candidate creation, retrieval, and listing."""
    candidate = repository.create_candidate(
        db=db_session,
        full_name="Sarah Connor",
        email="sarah@example.com",
        phone="555-0199",
        resume_text="Senior Systems Engineer with 8 years of Python experience.",
        parsed_resume_data={"skills": ["Python", "Docker"]},
    )
    assert candidate.id is not None
    assert candidate.full_name == "Sarah Connor"
    assert candidate.created_at is not None

    fetched = repository.get_candidate(db_session, candidate.id)
    assert fetched is not None
    assert fetched.email == "sarah@example.com"
    assert fetched.parsed_resume_data["skills"] == ["Python", "Docker"]

    candidates = repository.list_candidates(db_session)
    assert len(candidates) == 1
    assert candidates[0].id == candidate.id


def test_job_crud(db_session):
    """Test job posting creation, retrieval, and listing."""
    job = repository.create_job(
        db=db_session,
        title="Senior Python Backend Architect",
        company="TechCorp",
        description="Looking for an experienced engineer in FastAPI and PostgreSQL.",
        parsed_job_data={"required_skills": ["Python", "FastAPI", "PostgreSQL"]},
    )
    assert job.id is not None
    assert job.title == "Senior Python Backend Architect"
    assert job.company == "TechCorp"

    fetched = repository.get_job(db_session, job.id)
    assert fetched is not None
    assert fetched.title == job.title

    jobs = repository.list_jobs(db_session)
    assert len(jobs) == 1


def test_analysis_run_lifecycle(db_session):
    """Test creating and updating analysis runs linked to candidate and job."""
    candidate = repository.create_candidate(db_session, full_name="John Doe")
    job = repository.create_job(db_session, title="Backend Developer", description="Build APIs")

    analysis = repository.create_analysis_run(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        status="pending",
    )
    assert analysis.id is not None
    assert analysis.status == "pending"
    assert analysis.candidate_id == candidate.id
    assert analysis.job_id == job.id

    # Update analysis with completed results
    updated = repository.update_analysis_status(
        db=db_session,
        analysis_id=analysis.id,
        status="completed",
        match_result={"match_score": 88, "summary": "Strong candidate"},
        skill_gap_result={"missing_skills": ["Go"]},
    )
    assert updated.status == "completed"
    assert updated.completed_at is not None
    assert updated.match_result["match_score"] == 88

    analyses = repository.list_candidate_analyses(db_session, candidate.id)
    assert len(analyses) == 1
    assert analyses[0].id == analysis.id


def test_interview_session_questions_and_answers(db_session):
    """Test session creation, bulk questions insertion, and answer recording."""
    candidate = repository.create_candidate(db_session, full_name="Jane Doe")
    job = repository.create_job(db_session, title="ML Engineer", description="Build ML pipelines")

    session = repository.create_interview_session(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
    )
    assert session.id is not None
    assert session.status == "pending"
    assert session.total_questions == 0

    # Add questions
    q_data = [
        {
            "id": "TECH_01",
            "question": "What is Python GIL?",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["Thread safety", "Single core limitation"],
        },
        {
            "id": "TECH_02",
            "question": "Explain async/await in Python.",
            "category": "technical",
            "difficulty": "hard",
            "expected_points": ["Event loop", "Coroutines"],
        },
    ]
    questions = repository.add_interview_questions(db_session, session.id, q_data)
    assert len(questions) == 2
    assert questions[0].sequence_number == 1
    assert questions[1].sequence_number == 2

    # Refresh session
    db_session.refresh(session)
    assert session.total_questions == 2
    assert session.status == "in_progress"

    # Save answer for question 1
    answer = repository.save_interview_answer(
        db=db_session,
        question_id=questions[0].id,
        answer_text="The GIL is a mutex that prevents multiple native threads from executing Python bytecodes at once.",
        evaluation_result={"score": 9.5, "feedback": "Accurate definition."},
        score=9.5,
    )
    assert answer.id is not None
    assert answer.score == 9.5

    # Retrieve answers for session
    answers = repository.get_interview_answers(db_session, session.id)
    assert len(answers) == 1
    assert answers[0].id == answer.id


def test_duplicate_answer_constraint(db_session):
    """Ensure duplicate answer submissions for the same question are rejected."""
    candidate = repository.create_candidate(db_session, full_name="Candidate A")
    job = repository.create_job(db_session, title="DevOps", description="K8s and Terraform")
    session = repository.create_interview_session(db_session, candidate.id, job.id)

    q_data = [{"id": "Q1", "question": "Explain Docker.", "category": "DevOps", "difficulty": "easy"}]
    questions = repository.add_interview_questions(db_session, session.id, q_data)

    # First answer succeeds
    repository.save_interview_answer(
        db=db_session,
        question_id=questions[0].id,
        answer_text="Docker is a containerization platform.",
    )

    # Second answer for same question raises ValueError
    with pytest.raises(ValueError, match="already been answered"):
        repository.save_interview_answer(
            db=db_session,
            question_id=questions[0].id,
            answer_text="Attempting to submit another answer.",
        )


def test_cascade_delete_candidate(db_session):
    """Ensure deleting a candidate cascades cleanly to analysis and interview entities."""
    candidate = repository.create_candidate(db_session, full_name="Candidate Cascade")
    job = repository.create_job(db_session, title="Role", description="Desc")

    analysis = repository.create_analysis_run(db_session, candidate.id, job.id)
    session = repository.create_interview_session(db_session, candidate.id, job.id, analysis_run_id=analysis.id)
    questions = repository.add_interview_questions(
        db_session, session.id, [{"id": "Q1", "question": "Q?", "category": "General", "difficulty": "easy"}]
    )
    repository.save_interview_answer(db_session, questions[0].id, answer_text="Answer")

    # Delete candidate
    db_session.delete(candidate)
    db_session.commit()

    # Candidate should be gone
    assert repository.get_candidate(db_session, candidate.id) is None
    # Cascaded analysis and session should be gone
    assert repository.get_analysis_run(db_session, analysis.id) is None
    assert repository.get_interview_session(db_session, session.id) is None


def test_hiring_report_crud(db_session):
    """Test creating and retrieving persistent hiring reports."""
    candidate = repository.create_candidate(db_session, full_name="Report Candidate")
    job = repository.create_job(db_session, title="Data Engineer", description="ETL pipelines")
    analysis = repository.create_analysis_run(db_session, candidate.id, job.id, status="completed")

    report = repository.create_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        report_data={"executive_summary": "Exemplary candidate", "recommendation": "Strong Hire"},
        recommendation="Strong Hire",
        overall_score=94.5,
    )
    assert report.id is not None
    assert report.recommendation == "Strong Hire"
    assert report.overall_score == 94.5

    fetched = repository.get_hiring_report(db_session, report.id)
    assert fetched is not None
    assert fetched.analysis_run_id == analysis.id

    by_analysis = repository.get_report_by_analysis_id(db_session, analysis.id)
    assert by_analysis is not None
    assert by_analysis.id == report.id


def test_transaction_rollback(db_session):
    """Test that failed transactions roll back cleanly without persisting partial state."""
    candidate = repository.create_candidate(db_session, full_name="Valid Candidate")
    assert repository.get_candidate(db_session, candidate.id) is not None

    # Intentionally trigger an error in a transaction
    try:
        # Invalid insert: non-existent foreign key candidate_id in SQLite
        db_session.begin_nested()
        broken_session = InterviewSession(
            candidate_id="invalid-id",
            job_id="invalid-job",
        )
        db_session.add(broken_session)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Original candidate should still exist and DB session remains valid
    refetched = repository.get_candidate(db_session, candidate.id)
    assert refetched is not None
    assert refetched.full_name == "Valid Candidate"

