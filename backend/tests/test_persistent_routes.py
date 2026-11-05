"""
REST API Route Tests for Phase 3 Persistent Endpoints.
Tests Candidate, Job, Analysis, Stateful Interview Session, and Persistent Report endpoints.
"""
import json
import pytest

from tests.conftest import MockLLM, MockAIMessage
from agents.jd_parser import parser as jd_parser
from agents.resume_matcher import parser as rm_parser
from agents.skill_gap import parser as sg_parser
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


def test_candidate_routes(test_client):
    """Test POST, GET, and LIST endpoints for candidates."""
    # 1. Create candidate
    create_resp = test_client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Alan Turing",
            "email": "alan@enigma.org",
            "phone": "+44 123456789",
            "resume_text": "Pioneer of theoretical computer science.",
            "parsed_resume_data": {"skills": ["Cryptography", "Algorithms"]},
        },
    )
    assert create_resp.status_code == 201
    cand_data = create_resp.json()
    assert cand_data["id"] is not None
    assert cand_data["full_name"] == "Alan Turing"
    cand_id = cand_data["id"]

    # 2. Get candidate by ID
    get_resp = test_client.get(f"/api/v1/candidates/{cand_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "alan@enigma.org"

    # 3. Get non-existent candidate
    not_found = test_client.get("/api/v1/candidates/00000000-0000-0000-0000-000000000000")
    assert not_found.status_code == 404

    # 4. List candidates
    list_resp = test_client.get("/api/v1/candidates?skip=0&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


def test_job_routes(monkeypatch, test_client, synthetic_jd):
    """Test POST, GET, and LIST endpoints for jobs, and regression on /jobs/parse."""
    # 1. Create job
    create_resp = test_client.post(
        "/api/v1/jobs",
        json={
            "title": "Principal AI Architect",
            "company": "DeepTech",
            "description": "Architect end-to-end multi-agent AI platforms using Gemini.",
            "parsed_job_data": synthetic_jd,
        },
    )
    assert create_resp.status_code == 201
    job_data = create_resp.json()
    assert job_data["id"] is not None
    assert job_data["title"] == "Principal AI Architect"
    job_id = job_data["id"]

    # 2. Get job by ID
    get_resp = test_client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["company"] == "DeepTech"

    # 3. List jobs
    list_resp = test_client.get("/api/v1/jobs")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 4. Regression check on existing /jobs/parse endpoint
    monkeypatch.setattr(jd_parser, "llm", MockLLM(json.dumps(synthetic_jd)))
    parse_resp = test_client.post(
        "/api/v1/jobs/parse",
        json={"job_description": "We need a Senior Python Developer with FastAPI and cloud experience."},
    )
    assert parse_resp.status_code == 200
    assert "role_overview" in parse_resp.json() or "job_title" in parse_resp.json()


def test_analysis_routes(monkeypatch, test_client, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap):
    """Test analysis creation, retrieval, and candidate analysis listing."""
    # Create candidate and job
    c_resp = test_client.post(
        "/api/v1/candidates",
        json={"full_name": "Grace Hopper", "parsed_resume_data": synthetic_resume},
    )
    cand_id = c_resp.json()["id"]

    j_resp = test_client.post(
        "/api/v1/jobs",
        json={
            "title": "Systems Lead",
            "description": "COBOL and modern distributed systems engineering",
            "parsed_job_data": synthetic_jd,
        },
    )
    job_id = j_resp.json()["id"]

    monkeypatch.setattr(rm_parser, "llm", MockLLM(json.dumps(synthetic_match)))
    monkeypatch.setattr(sg_parser, "llm", MockLLM(json.dumps(synthetic_skill_gap)))

    run_resp = test_client.post(
        "/api/v1/analysis",
        json={"candidate_id": cand_id, "job_id": job_id},
    )

    assert run_resp.status_code == 201
    analysis_data = run_resp.json()
    assert analysis_data["id"] is not None
    assert analysis_data["status"] == "completed"
    analysis_id = analysis_data["id"]

    # Get analysis run by ID
    get_run = test_client.get(f"/api/v1/analysis/{analysis_id}")
    assert get_run.status_code == 200
    assert get_run.json()["candidate_id"] == cand_id

    # List candidate analyses
    cand_analyses = test_client.get(f"/api/v1/candidates/{cand_id}/analysis")
    assert cand_analyses.status_code == 200
    assert cand_analyses.json()["total"] == 1


def test_interview_session_and_answers_routes(monkeypatch, test_client, synthetic_summary):
    """Test complete persistent interview lifecycle through REST endpoints."""
    # Create candidate and job
    cand_id = test_client.post("/api/v1/candidates", json={"full_name": "Ada Lovelace"}).json()["id"]
    job_id = test_client.post(
        "/api/v1/jobs",
        json={"title": "Algorithm Engineer", "description": "Mathematical algorithm and computing design"},
    ).json()["id"]

    # 1. Create interview session with custom questions
    custom_qs = [
        {"id": "ALGO_01", "question": "Explain Big O notation.", "category": "Algorithms", "difficulty": "easy"},
        {"id": "ALGO_02", "question": "What is dynamic programming?", "category": "Algorithms", "difficulty": "medium"},
    ]
    create_session = test_client.post(
        "/api/v1/interviews",
        json={
            "candidate_id": cand_id,
            "job_id": job_id,
            "generate_questions": False,
            "custom_questions": custom_qs,
        },
    )
    assert create_session.status_code == 201
    session_data = create_session.json()
    session_id = session_data["session_id"]
    assert session_data["total_questions"] == 2
    assert session_data["answered_questions_count"] == 0

    # 2. Get questions
    q_resp = test_client.get(f"/api/v1/interviews/{session_id}/questions")
    assert q_resp.status_code == 200
    questions = q_resp.json()
    assert len(questions) == 2
    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]

    # 3. Submit first answer
    mock_eval = {
        "score": 9.2,
        "strengths": ["Clear asymptotic bounds explanation"],
        "weaknesses": [],
        "feedback": "Great clarity.",
        "score_explanation": "Good answer.",
    }
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps(mock_eval)))

    ans_resp = test_client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"question_id": q1_id, "answer": "Big O describes the upper bound of runtime complexity."},
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert ans_data["score"] == 9.2
    assert ans_data["current_question_index"] == 1
    assert ans_data["is_interview_completed"] is False

    # 4. Submit duplicate answer on question 1 -> 400
    dup_resp = test_client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"question_id": q1_id, "answer": "Attempting duplicate answer"},
    )
    assert dup_resp.status_code == 400

    # 5. List answers
    list_ans = test_client.get(f"/api/v1/interviews/{session_id}/answers")
    assert list_ans.status_code == 200
    assert len(list_ans.json()) == 1

    # 6. Submit second answer (should trigger auto-completion)
    seq_llm = SequentialMockLLM([json.dumps(mock_eval), json.dumps(synthetic_summary)])
    monkeypatch.setattr(ie_evaluator, "llm", seq_llm)

    ans2_resp = test_client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"question_id": q2_id, "answer": "DP breaks problems into overlapping subproblems."},
    )
    assert ans2_resp.status_code == 200
    assert ans2_resp.json()["is_interview_completed"] is True
    assert ans2_resp.json()["session_status"] == "completed"

    # 7. Get session details after completion
    session_detail = test_client.get(f"/api/v1/interviews/{session_id}")
    assert session_detail.status_code == 200
    assert session_detail.json()["status"] == "completed"
    assert session_detail.json()["final_summary"] is not None


def test_persistent_reports_routes(
    monkeypatch, test_client, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_summary, synthetic_report
):
    """Test persistent report generation and retrieval by report ID and analysis ID."""
    cand_id = test_client.post("/api/v1/candidates", json={"full_name": "Claude Shannon", "parsed_resume_data": synthetic_resume}).json()["id"]
    job_id = test_client.post(
        "/api/v1/jobs",
        json={"title": "Information Theorist", "description": "Mathematical communications and entropy modeling", "parsed_job_data": synthetic_jd},
    ).json()["id"]

    monkeypatch.setattr(rm_parser, "llm", MockLLM(json.dumps(synthetic_match)))
    monkeypatch.setattr(sg_parser, "llm", MockLLM(json.dumps(synthetic_skill_gap)))

    analysis_id = test_client.post("/api/v1/analysis", json={"candidate_id": cand_id, "job_id": job_id}).json()["id"]

    # Generate persistent report
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(synthetic_report)))
    rep_resp = test_client.post(
        "/api/v1/reports",
        json={"analysis_run_id": analysis_id},
    )
    assert rep_resp.status_code == 201
    rep_data = rep_resp.json()
    assert rep_data["id"] is not None
    assert rep_data["recommendation"] == "Hire"
    report_id = rep_data["id"]

    # Get report by report ID
    get_rep = test_client.get(f"/api/v1/reports/{report_id}")
    assert get_rep.status_code == 200
    assert get_rep.json()["recommendation"] == "Hire"

    # Get report by analysis ID
    by_analysis = test_client.get(f"/api/v1/analysis/{analysis_id}/report")
    assert by_analysis.status_code == 200
    assert by_analysis.json()["id"] == report_id
