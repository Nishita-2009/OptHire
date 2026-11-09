"""
Interview Workflow Service Tests.
Tests stateful session transitions, Agent 5 generation, Agent 6 evaluation,
progress tracking, final interview summary aggregation, and report generation.
"""
import copy
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
    assert db_report.is_provisional is False


def test_report_authoritative_metadata_overrides_stale_parsed_json(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Ensure database entity metadata (full_name, title) authoritatively overrides stale parsed JSON."""
    stale_resume = dict(synthetic_resume)
    stale_resume["name"] = "Stale Conflicting Name"

    stale_jd = dict(synthetic_jd)
    stale_jd["job_title"] = "Stale Conflicting Role"

    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=stale_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", company="TechNova Solutions", description="Python development", parsed_job_data=stale_jd)
    analysis = repository.create_analysis_run(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        status="completed",
        resume_parse_result=stale_resume,
        job_parse_result=stale_jd,
        match_result=synthetic_match,
        skill_gap_result=synthetic_skill_gap,
    )
    session = repository.create_interview_session(
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="completed"
    )
    session.final_summary = synthetic_summary
    db_session.commit()

    # Model might echo synthetic report which had Alex Morgan / Software Engineer
    mock_rep = dict(synthetic_report)
    mock_rep["candidate"] = dict(mock_rep["candidate"])
    mock_rep["candidate"]["name"] = "Model Echoed Name"
    mock_rep["candidate"]["target_role"] = "Model Echoed Role"

    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    # Authoritative entity metadata must prevail
    report_data = report_result["report_data"]
    assert report_data["candidate"]["name"] == "Alex Morgan"
    assert report_data["candidate"]["target_role"] == "Junior Python Developer"
    assert report_result["is_provisional"] is False


def test_report_with_one_evaluated_answer_score_85(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_report
):
    """
    Test user's exact observed scenario:
    - 21 questions total
    - 1 answer submitted with score 85.0
    - Session remains in_progress
    - Report is clearly generated as Provisional with interview_score=85.0
    """
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", description="Junior Python engineer role", parsed_job_data=synthetic_jd)
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

    # Create session with 21 questions
    session = repository.create_interview_session(
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="in_progress"
    )
    questions_data = [
        {"id": f"Q_{i:02d}", "question": f"Question {i}", "category": "Tech", "difficulty": "medium"}
        for i in range(1, 22)
    ]
    created_questions = repository.add_interview_questions(db_session, session.id, questions_data)
    assert len(created_questions) == 21

    # Submit exactly 1 answer with evaluation score 85.0
    q1 = created_questions[0]
    eval_result = {
        "score": 85,
        "rating": "Strong",
        "answer_summary": "Accurately explains async/await in FastAPI.",
        "strengths": ["Clear definition of coroutines and event loop non-blocking behavior."],
        "missing_points": [],
        "feedback": "Concise and accurate explanation.",
        "question_id": q1.question_identifier,
        "question": q1.question_text,
        "candidate_answer": "In Python, async and await are used for asynchronous programming without blocking the event loop.",
        "category": q1.category,
    }
    repository.save_interview_answer(
        db=db_session,
        question_id=q1.id,
        answer_text="In Python, async and await are used for asynchronous programming without blocking the event loop.",
        evaluation_result=eval_result,
        score=85.0,
    )

    # Ensure session remains in_progress
    db_session.refresh(session)
    assert session.status == "in_progress"
    assert session.final_summary is None

    mock_rep = dict(synthetic_report)
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    # 1. Provisional report flag and details
    assert report_result["is_provisional"] is True
    report_data = report_result["report_data"]
    assert report_data["is_provisional"] is True
    assert "Provisional" in report_data["report_title"]

    prov = report_data["provisional_details"]
    assert prov["is_provisional"] is True
    assert prov["session_status"] == "in_progress"
    assert prov["questions_answered"] == 1
    assert prov["total_questions"] == 21
    assert prov["evaluated_count"] == 1
    assert prov["partial_interview_score"] == 85.0
    assert "85.0/100" in prov["score_calculation"]

    # 2. Score and confidence
    assert report_data["scores"]["interview_score"] == 85.0
    assert report_data["scores"]["decision_confidence"] <= 60

    # 3. Authoritative candidate and job metadata
    assert report_data["candidate"]["name"] == "Alex Morgan"
    assert report_data["candidate"]["target_role"] == "Junior Python Developer"

    # 4. Session MUST remain open so candidate can answer remaining questions
    db_session.refresh(session)
    assert session.status == "in_progress"
    assert session.completed_at is None


def test_report_zero_answer_session_not_started(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_report
):
    """Ensure a session with 0 answers is reported as Not Started without claiming interview occurred."""
    candidate = repository.create_candidate(db_session, full_name="Bob", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Dev", description="Python dev position", parsed_job_data=synthetic_jd)
    analysis = repository.create_analysis_run(
        db_session, candidate_id=candidate.id, job_id=job.id, status="completed",
        resume_parse_result=synthetic_resume, job_parse_result=synthetic_jd,
        match_result=synthetic_match, skill_gap_result=synthetic_skill_gap,
    )
    session = repository.create_interview_session(
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="pending"
    )
    repository.add_interview_questions(db_session, session.id, [{"id": "Q1", "question": "Q?", "category": "General", "difficulty": "easy"}])

    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(synthetic_report)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    assert report_result["is_provisional"] is True
    prov = report_result["report_data"]["provisional_details"]
    assert prov["questions_answered"] == 0
    assert prov["partial_interview_score"] == 0.0
    assert report_result["report_data"]["scores"]["interview_score"] == 0


def test_report_missing_or_invalid_evaluation_scores(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_report
):
    """Ensure partial score calculation uses only valid, non-null evaluation scores."""
    candidate = repository.create_candidate(db_session, full_name="Charlie", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Dev", description="Python dev position", parsed_job_data=synthetic_jd)
    analysis = repository.create_analysis_run(
        db_session, candidate_id=candidate.id, job_id=job.id, status="completed",
        resume_parse_result=synthetic_resume, job_parse_result=synthetic_jd,
        match_result=synthetic_match, skill_gap_result=synthetic_skill_gap,
    )
    session = repository.create_interview_session(
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="in_progress"
    )
    qs = repository.add_interview_questions(
        db_session, session.id,
        [
            {"id": "Q1", "question": "Q1?", "category": "Tech", "difficulty": "easy"},
            {"id": "Q2", "question": "Q2?", "category": "Tech", "difficulty": "easy"},
        ]
    )

    # Answer 1 has valid evaluation score 80.0
    repository.save_interview_answer(
        db=db_session, question_id=qs[0].id, answer_text="Ans 1", evaluation_result={"score": 80}, score=80.0
    )
    # Answer 2 has no evaluation result or score
    repository.save_interview_answer(
        db=db_session, question_id=qs[1].id, answer_text="Ans 2", evaluation_result=None, score=None
    )

    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(synthetic_report)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    prov = report_result["report_data"]["provisional_details"]
    assert prov["questions_answered"] == 2
    assert prov["evaluated_count"] == 1
    # Only the valid score (80.0) is factored in
    assert prov["partial_interview_score"] == 80.0
    assert report_result["report_data"]["scores"]["interview_score"] == 80.0


def test_database_job_title_overrides_stale_parsed_job_json(
    monkeypatch, db_session, synthetic_resume, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Database job title must authoritatively override any stale parsed job JSON."""
    stale_parsed_jd = {
        "job_title": "Senior C++ Architect",
        "title": "Senior C++ Architect",
        "required_skills": ["C++", "Templates"],
    }
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(
        db_session,
        title="Junior Python Developer",
        company="TechNova Solutions",
        description="Python API developer",
        parsed_job_data=stale_parsed_jd,
    )
    analysis = repository.create_analysis_run(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        status="completed",
        resume_parse_result=synthetic_resume,
        job_parse_result=stale_parsed_jd,
        match_result=synthetic_match,
        skill_gap_result=synthetic_skill_gap,
    )
    session = repository.create_interview_session(
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="completed"
    )
    session.final_summary = synthetic_summary
    db_session.commit()

    mock_rep = copy.deepcopy(synthetic_report)
    mock_rep["candidate"]["target_role"] = "Senior C++ Architect"
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    report_data = report_result["report_data"]
    assert report_data["candidate"]["target_role"] == "Junior Python Developer"
    assert "Senior C++ Architect" not in report_data["candidate"]["target_role"]


def test_candidate_summary_uses_authoritative_job_title(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Candidate summary narrative must reference authoritative job title and remove conflicting titles."""
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", company="TechNova Solutions", description="Python development", parsed_job_data=synthetic_jd)
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

    mock_rep = copy.deepcopy(synthetic_report)
    # Simulate LLM outputting the exact observed issue:
    mock_rep["candidate"]["candidate_summary"] = (
        "The candidate is an excellent match for this entry-level Backend Developer position. "
        "They possess all required technical skills and their experience level perfectly aligns with the job description."
    )
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    candidate_sec = report_result["report_data"]["candidate"]
    assert "Junior Python Developer" in candidate_sec["candidate_summary"]
    assert "Backend Developer" not in candidate_sec["candidate_summary"]
    assert candidate_sec["name"] == "Alex Morgan"
    assert candidate_sec["target_role"] == "Junior Python Developer"


def test_executive_summary_uses_authoritative_job_title(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Executive summary narrative must reference authoritative candidate name and job title."""
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", company="TechNova Solutions", description="Python development", parsed_job_data=synthetic_jd)
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

    mock_rep = copy.deepcopy(synthetic_report)
    mock_rep["executive_summary"] = (
        "The candidate presents an exceptionally strong resume for the entry-level Backend Developer role, "
        "demonstrating a 94% ATS match with all required technical skills and a perfect experience alignment."
    )
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    exec_summary = report_result["report_data"]["executive_summary"]
    assert "Junior Python Developer" in exec_summary
    assert "Alex Morgan" in exec_summary
    assert "Backend Developer" not in exec_summary


def test_conflicting_generic_titles_do_not_appear_in_generated_narrative_fields(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Conflicting generic titles like Backend Developer or Software Engineer must not appear across narrative fields."""
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", company="TechNova Solutions", description="Python development", parsed_job_data=synthetic_jd)
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

    mock_rep = copy.deepcopy(synthetic_report)
    mock_rep["candidate"]["candidate_summary"] = "Match for entry-level Backend Developer position."
    mock_rep["executive_summary"] = "Ideal match for Backend Developer role."
    mock_rep["resume_evaluation"]["summary"] = "Foundational match for Backend Developer position."
    mock_rep["resume_evaluation"]["key_strengths"] = ["Strong fit for Backend Developer role."]
    mock_rep["final_decision"]["reasoning"] = "Candidate is qualified for the Backend Developer position."
    mock_rep["key_reasons_to_hire"] = ["Meets requirements for Software Engineer job."]
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    data = report_result["report_data"]
    # Verify candidate_summary
    assert "Junior Python Developer" in data["candidate"]["candidate_summary"]
    assert "Backend Developer" not in data["candidate"]["candidate_summary"]

    # Verify executive_summary
    assert "Junior Python Developer" in data["executive_summary"]
    assert "Backend Developer" not in data["executive_summary"]

    # Verify resume summary
    assert "Junior Python Developer" in data["resume_evaluation"]["summary"]
    assert "Backend Developer" not in data["resume_evaluation"]["summary"]

    # Verify key_strengths
    for s in data["resume_evaluation"]["key_strengths"]:
        assert "Backend Developer" not in s

    # Verify final_decision reasoning
    assert "Junior Python Developer" in data["final_decision"]["reasoning"]
    assert "Backend Developer" not in data["final_decision"]["reasoning"]

    # Verify key_reasons_to_hire
    for r in data["key_reasons_to_hire"]:
        assert "Software Engineer" not in r


def test_provisional_reports_remain_provisional_when_interview_incomplete(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_report
):
    """Provisional reports must remain provisional with correct scores and keep session open."""
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", company="TechNova Solutions", description="Python development", parsed_job_data=synthetic_jd)
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
        db_session, candidate_id=candidate.id, job_id=job.id, analysis_run_id=analysis.id, status="in_progress"
    )
    qs = repository.add_interview_questions(
        db_session,
        session.id,
        [
            {"id": f"Q{i}", "question": f"Question {i}", "category": "Tech", "difficulty": "medium"}
            for i in range(1, 6)
        ],
    )
    repository.save_interview_answer(
        db_session, question_id=qs[0].id, answer_text="Answer 1", evaluation_result={"score": 85}, score=85.0
    )

    mock_rep = copy.deepcopy(synthetic_report)
    mock_rep["candidate"]["candidate_summary"] = "The candidate is an excellent match for this entry-level Backend Developer position."
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    assert report_result["is_provisional"] is True
    assert report_result["report_data"]["is_provisional"] is True
    prov = report_result["report_data"]["provisional_details"]
    assert prov["partial_interview_score"] == 85.0
    assert prov["session_status"] == "in_progress"

    # Session remains in_progress
    refetched_session = repository.get_interview_session(db_session, session.id)
    assert refetched_session.status == "in_progress"
    assert refetched_session.completed_at is None

    # Narrative consistency
    assert "Junior Python Developer" in report_result["report_data"]["candidate"]["candidate_summary"]
    assert "Backend Developer" not in report_result["report_data"]["candidate"]["candidate_summary"]


def test_completed_interview_reports_continue_using_final_interview_summary(
    monkeypatch, db_session, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Completed interview sessions must generate final non-provisional reports using final_summary."""
    candidate = repository.create_candidate(db_session, full_name="Alex Morgan", parsed_resume_data=synthetic_resume)
    job = repository.create_job(db_session, title="Junior Python Developer", company="TechNova Solutions", description="Python development", parsed_job_data=synthetic_jd)
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
    completed_summary = dict(synthetic_summary)
    completed_summary["overall_interview_score"] = 92.0
    session.final_summary = completed_summary
    db_session.commit()

    mock_rep = copy.deepcopy(synthetic_report)
    mock_rep["scores"]["interview_score"] = 92.0
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(mock_rep)))

    report_result = InterviewService.generate_and_save_hiring_report(
        db=db_session,
        analysis_run_id=analysis.id,
        interview_session_id=session.id,
    )

    assert report_result["is_provisional"] is False
    assert report_result["report_data"]["is_provisional"] is False
    assert report_result["report_data"]["candidate"]["name"] == "Alex Morgan"
    assert report_result["report_data"]["candidate"]["target_role"] == "Junior Python Developer"
    assert report_result["report_data"]["scores"]["interview_score"] == 92.0


