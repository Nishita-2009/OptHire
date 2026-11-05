"""
Interview Workflow Service Tests.
Tests stateful session transitions, Agent 5 generation, Agent 6 evaluation,
progress tracking, final interview summary aggregation, and report generation.
"""
import json
import pytest

from services.interview_service import InterviewService
from database import repository
from tests.conftest import MockLLM, MockAIMessage
from agents.interview_generator import parser as ig_parser
from agents.interview_evaluator import evaluator as ie_evaluator
from agents.hiring_report import generator as hr_generator


class SequentialMockLLM:
    """Mock LLM that yields consecutive responses for multiple calls."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.index = 0

    def invoke(self, prompt):
        if self.index < len(self.responses):
            val = self.responses[self.index]
            self.index += 1
            return MockAIMessage(val)
        return MockAIMessage(self.responses[-1])


def test_create_session_with_generated_questions(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_interview
):
    """Test session initialization generating 21 questions via Agent 5."""
    candidate = repository.create_candidate(
        db_session, full_name="Alice Smith", parsed_resume_data=synthetic_resume
    )
    job = repository.create_job(
        db_session, title="Backend Engineer", description="Python and FastAPI senior engineer", parsed_job_data=synthetic_jd
    )
    analysis = repository.create_analysis_run(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        match_result=synthetic_match,
        skill_gap_result=synthetic_skill_gap,
    )

    monkeypatch.setattr(ig_parser, "llm", MockLLM(json.dumps(synthetic_interview)))

    session = InterviewService.create_session(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        analysis_run_id=analysis.id,
        generate_questions=True,
    )

    assert session.id is not None
    assert session.total_questions == 21
    assert session.status == "in_progress"
    assert session.current_question_index == 0

    questions = repository.get_interview_questions(db_session, session.id)
    assert len(questions) == 21
    assert questions[0].sequence_number == 1
    assert questions[20].sequence_number == 21


def test_create_session_candidate_or_job_not_found(db_session):
    """Ensure invalid candidate or job ID raises ValueError."""
    candidate = repository.create_candidate(db_session, full_name="Alice")

    with pytest.raises(ValueError, match="Job non-existent-job not found"):
        InterviewService.create_session(
            db=db_session,
            candidate_id=candidate.id,
            job_id="non-existent-job",
        )

    with pytest.raises(ValueError, match="Candidate non-existent-candidate not found"):
        InterviewService.create_session(
            db=db_session,
            candidate_id="non-existent-candidate",
            job_id="some-job",
        )


def test_submit_and_evaluate_answer(monkeypatch, db_session):
    """Test candidate answer submission, Agent 6 evaluation, and progress calculation."""
    candidate = repository.create_candidate(db_session, full_name="Bob")
    job = repository.create_job(db_session, title="Cloud Architect", description="AWS & GCP cloud infrastructure engineering")

    session = InterviewService.create_session(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        generate_questions=False,
        custom_questions=[
            {
                "id": "CLOUD_01",
                "question": "What is Infrastructure as Code?",
                "category": "Cloud",
                "difficulty": "medium",
                "expected_points": ["Declarative configuration", "Version control"],
            },
            {
                "id": "CLOUD_02",
                "question": "Explain serverless architecture.",
                "category": "Cloud",
                "difficulty": "hard",
            },
        ],
    )
    assert session.total_questions == 2

    questions = repository.get_interview_questions(db_session, session.id)
    q1 = questions[0]

    mock_eval = {
        "score": 9.0,
        "strengths": ["Clear explanation of IaC concepts"],
        "weaknesses": [],
        "feedback": "Outstanding answer.",
        "score_explanation": "Covered declarative setup.",
    }
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps(mock_eval)))

    result = InterviewService.submit_and_evaluate_answer(
        db=db_session,
        session_id=session.id,
        question_id=q1.id,
        answer_text="IaC is managing and provisioning computer data centers through machine-readable definition files.",
    )

    assert result["session_id"] == session.id
    assert result["score"] == 9.0
    assert result["current_question_index"] == 1
    assert result["total_questions"] == 2
    assert result["is_interview_completed"] is False

    # Verify session details reflect progress
    details = InterviewService.get_session_details(db_session, session.id)
    assert details["answered_questions_count"] == 1
    assert details["current_question"]["id"] == questions[1].id


def test_submit_duplicate_and_empty_answer(monkeypatch, db_session):
    """Ensure duplicate answer submissions or empty answers are rejected."""
    candidate = repository.create_candidate(db_session, full_name="Charlie")
    job = repository.create_job(db_session, title="Engineer", description="Software Engineer role with backend focus")
    session = InterviewService.create_session(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        generate_questions=False,
        custom_questions=[
            {"id": "Q1", "question": "Question 1", "category": "General", "difficulty": "easy"},
            {"id": "Q2", "question": "Question 2", "category": "General", "difficulty": "easy"},
        ],
    )
    questions = repository.get_interview_questions(db_session, session.id)
    q1 = questions[0]

    # Empty answer rejected
    with pytest.raises(ValueError, match="cannot be empty"):
        InterviewService.submit_and_evaluate_answer(
            db=db_session, session_id=session.id, question_id=q1.id, answer_text="   "
        )

    # Valid answer accepted
    mock_eval = {"score": 8.0, "feedback": "Good answer"}
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps(mock_eval)))
    InterviewService.submit_and_evaluate_answer(
        db=db_session, session_id=session.id, question_id=q1.id, answer_text="Valid answer"
    )

    # Duplicate answer on same question rejected
    with pytest.raises(ValueError, match="already been answered"):
        InterviewService.submit_and_evaluate_answer(
            db=db_session, session_id=session.id, question_id=q1.id, answer_text="Another attempt"
        )


def test_session_auto_completion_on_final_question(monkeypatch, db_session, synthetic_summary):
    """Ensure answering all questions auto-finalizes session and triggers summary generation."""
    candidate = repository.create_candidate(db_session, full_name="Dan")
    job = repository.create_job(db_session, title="Dev", description="Backend Developer building scalable microservices")

    session = InterviewService.create_session(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        generate_questions=False,
        custom_questions=[{"id": "Q1", "question": "Final Q", "category": "Tech", "difficulty": "easy"}],
    )
    q1 = repository.get_interview_questions(db_session, session.id)[0]

    mock_eval = {"score": 10.0, "feedback": "Perfect"}
    seq_llm = SequentialMockLLM([json.dumps(mock_eval), json.dumps(synthetic_summary)])
    monkeypatch.setattr(ie_evaluator, "llm", seq_llm)

    result = InterviewService.submit_and_evaluate_answer(
        db=db_session,
        session_id=session.id,
        question_id=q1.id,
        answer_text="Complete answer.",
    )

    assert result["is_interview_completed"] is True
    assert result["session_status"] == "completed"

    # Confirm session state in DB
    completed = repository.get_interview_session(db_session, session.id)
    assert completed.status == "completed"
    assert completed.completed_at is not None
    assert completed.final_summary is not None


def test_explicit_session_finalization(monkeypatch, db_session, synthetic_summary):
    """Test explicit completion of an interview session."""
    candidate = repository.create_candidate(db_session, full_name="Eve")
    job = repository.create_job(db_session, title="Dev", description="Full stack software engineer position")

    session = InterviewService.create_session(
        db=db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        generate_questions=False,
        custom_questions=[
            {"id": "Q1", "question": "Question 1", "category": "Tech", "difficulty": "easy"},
            {"id": "Q2", "question": "Question 2", "category": "Tech", "difficulty": "easy"},
        ],
    )
    q1 = repository.get_interview_questions(db_session, session.id)[0]

    # Cannot finalize without answers
    with pytest.raises(ValueError, match="no answers have been submitted"):
        InterviewService.finalize_interview_session(db_session, session.id)

    # Submit 1 answer
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps({"score": 7.0, "feedback": "Fair"})))
    InterviewService.submit_and_evaluate_answer(
        db=db_session, session_id=session.id, question_id=q1.id, answer_text="My answer"
    )

    # Now finalize explicitly
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps(synthetic_summary)))
    finalized = InterviewService.finalize_interview_session(db_session, session.id)

    assert finalized.status == "completed"
    assert finalized.final_summary is not None


def test_generate_and_save_hiring_report(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Test generating and persisting a final hiring report via Agent 7."""
    candidate = repository.create_candidate(db_session, full_name="Frank", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Lead", description="Lead Systems Engineer designing cloud architecture", parsed_job_data=synthetic_jd)
    analysis = repository.create_analysis_run(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        status="completed",
        resume_parse_result=synthetic_resume,
        job_parse_result=synthetic_jd,
        match_result=synthetic_match,
        skill_gap_result=synthetic_skill_gap,
    )
    session = repository.create_interview_session(
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="completed"
    )
    session.final_summary = synthetic_summary
    db_session.commit()

    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(synthetic_report)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    assert report_result["id"] is not None
    assert report_result["analysis_run_id"] == analysis.id
    assert report_result["recommendation"] == "Hire"
    assert report_result["overall_score"] == 89.0

    # Verify report is in database
    db_report = repository.get_hiring_report(db_session, report_result["id"])
    assert db_report is not None
    assert db_report.analysis_run_id == analysis.id
