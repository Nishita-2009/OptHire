"""
Comprehensive FastAPI Route Tests for OptHire Backend.
Uses FastAPI TestClient with fully mocked agent boundaries to ensure
zero live Gemini API calls and zero quota consumption.
"""
import io
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    """Module-scoped FastAPI test client."""
    return TestClient(app)


# ============================================================================
# 1. HEALTH CHECK
# ============================================================================
def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "OptHire API"
    assert data["version"] == "1.0.0"


# ============================================================================
# 2. RESUME PARSING (AGENT 1)
# ============================================================================
def test_parse_resume_endpoint_success(client, monkeypatch, synthetic_resume):
    from api.routes import resumes

    # Mock Agent 1 boundary
    monkeypatch.setattr(resumes, "parse_resume", lambda text: synthetic_resume)

    dummy_pdf = b"%PDF-1.4 dummy pdf content for testing"
    files = {"file": ("test_resume.pdf", io.BytesIO(dummy_pdf), "application/pdf")}

    # Also mock text extraction to simulate reading PDF text
    monkeypatch.setattr(resumes, "extract_text_from_upload", lambda f: "Extracted candidate text")

    response = client.post("/api/v1/resumes/parse", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alex Morgan"
    assert "Python" in data["skills"]


def test_parse_resume_endpoint_unsupported_file_type(client):
    files = {"file": ("test.docx", io.BytesIO(b"dummy word doc"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/api/v1/resumes/parse", files=files)
    assert response.status_code == 415
    assert "Only PDF files are accepted" in response.json()["message"]


def test_parse_resume_endpoint_empty_file(client):
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/api/v1/resumes/parse", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()


def test_parse_resume_endpoint_upstream_error(client, monkeypatch):
    from api.routes import resumes

    monkeypatch.setattr(resumes, "extract_text_from_upload", lambda f: "Candidate text")

    def failing_parse(text):
        raise ValueError("Malformed JSON returned by Gemini")

    monkeypatch.setattr(resumes, "parse_resume", failing_parse)

    dummy_pdf = b"%PDF-1.4 content"
    files = {"file": ("resume.pdf", io.BytesIO(dummy_pdf), "application/pdf")}
    response = client.post("/api/v1/resumes/parse", files=files)
    assert response.status_code == 502
    assert "Failed to extract structured data" in response.json()["message"]


# ============================================================================
# 3. JOB DESCRIPTION PARSING (AGENT 2)
# ============================================================================
def test_parse_job_endpoint_success(client, monkeypatch, synthetic_jd):
    from api.routes import jobs

    monkeypatch.setattr(jobs, "parse_job_description", lambda jd: synthetic_jd)

    payload = {"job_description": "Looking for Senior Backend Developer with Python and FastAPI."}
    response = client.post("/api/v1/jobs/parse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Software Engineer (Backend)"
    assert "Python" in data["required_skills"]


def test_parse_job_endpoint_empty_or_short(client):
    # Too short (< 10 chars) triggers Pydantic schema validation (422)
    response = client.post("/api/v1/jobs/parse", json={"job_description": "Short"})
    assert response.status_code == 422


def test_parse_job_endpoint_upstream_error(client, monkeypatch):
    from api.routes import jobs

    def failing_parse_jd(jd):
        raise ValueError("Gemini invalid JSON")

    monkeypatch.setattr(jobs, "parse_job_description", failing_parse_jd)

    payload = {"job_description": "Looking for Senior Backend Developer with 5+ years experience."}
    response = client.post("/api/v1/jobs/parse", json=payload)
    assert response.status_code == 502
    assert "Failed to extract structured requirements" in response.json()["message"]


# ============================================================================
# 4. RESUME MATCHING (AGENT 3)
# ============================================================================
def test_match_resume_endpoint_success(client, monkeypatch, synthetic_resume, synthetic_jd, synthetic_match):
    from api.routes import match

    monkeypatch.setattr(match, "match_resume", lambda r, j: synthetic_match)

    payload = {
        "resume": synthetic_resume,
        "job_description": synthetic_jd,
    }
    response = client.post("/api/v1/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_match_score"] == 88
    assert "FastAPI" in data["matched_skills"]


def test_match_resume_endpoint_empty_inputs(client):
    response = client.post("/api/v1/match", json={"resume": {}, "job_description": {}})
    assert response.status_code == 400


def test_match_resume_endpoint_upstream_error(client, monkeypatch, synthetic_resume, synthetic_jd):
    from api.routes import match

    monkeypatch.setattr(match, "match_resume", lambda r, j: (_ for _ in ()).throw(ValueError("Upstream match error")))

    payload = {"resume": synthetic_resume, "job_description": synthetic_jd}
    response = client.post("/api/v1/match", json=payload)
    assert response.status_code == 502


# ============================================================================
# 5. SKILL GAP ANALYSIS (AGENT 4)
# ============================================================================
def test_skill_gap_endpoint_success(client, monkeypatch, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap):
    from api.routes import skill_gap

    monkeypatch.setattr(skill_gap, "analyze_skill_gap", lambda r, j, m: synthetic_skill_gap)

    payload = {
        "resume": synthetic_resume,
        "job_description": synthetic_jd,
        "match_result": synthetic_match,
    }
    response = client.post("/api/v1/skill-gap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["missing_skills"]) > 0
    assert data["missing_skills"][0]["skill"] == "Kubernetes"


def test_skill_gap_endpoint_missing_payload(client, synthetic_resume, synthetic_jd):
    # Missing match_result
    payload = {"resume": synthetic_resume, "job_description": synthetic_jd}
    response = client.post("/api/v1/skill-gap", json=payload)
    assert response.status_code == 422


# ============================================================================
# 6. INTERVIEW GENERATOR (AGENT 5)
# ============================================================================
def test_interview_generate_endpoint_success(
    client,
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_interview,
):
    from api.routes import interview

    monkeypatch.setattr(interview, "generate_interview", lambda **kwargs: synthetic_interview)

    payload = {
        "resume": synthetic_resume,
        "job_description": synthetic_jd,
        "match_result": synthetic_match,
        "skill_gap": synthetic_skill_gap,
    }
    response = client.post("/api/v1/interview/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["technical_questions"]) == 5
    assert len(data["coding_questions"]) == 3
    assert len(data["hr_questions"]) == 2
    assert data["question_distribution"]["total"] == 21


def test_interview_generate_endpoint_validation_failure(
    client,
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
):
    from api.routes import interview

    def bad_generate(**kwargs):
        raise ValueError("technical_questions should contain 5 questions, but Gemini returned 4.")

    monkeypatch.setattr(interview, "generate_interview", bad_generate)

    payload = {
        "resume": synthetic_resume,
        "job_description": synthetic_jd,
        "match_result": synthetic_match,
        "skill_gap": synthetic_skill_gap,
    }
    response = client.post("/api/v1/interview/generate", json=payload)
    assert response.status_code == 502
    assert "failed validation" in response.json()["message"]


# ============================================================================
# 7. INTERVIEW EVALUATOR (AGENT 6)
# ============================================================================
def test_interview_evaluate_endpoint_success(client, monkeypatch, synthetic_interview):
    from api.routes import interview

    question = synthetic_interview["technical_questions"][0]
    mock_eval = {
        "score": 90,
        "rating": "Strong",
        "answer_summary": "Solid technical explanation.",
        "strengths": ["Understanding of asyncio loop"],
        "missing_points": [],
        "feedback": "Great explanation.",
        "ideal_answer": "In FastAPI, async def...",
        "question_id": question["question_id"],
        "question": question["question"],
        "candidate_answer": "Async endpoints run non-blocking on event loop.",
        "category": "Technical",
    }
    monkeypatch.setattr(interview, "evaluate_answer", lambda question, candidate_answer: mock_eval)

    payload = {
        "question": question,
        "candidate_answer": "Async endpoints run non-blocking on event loop.",
    }
    response = client.post("/api/v1/interview/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 90
    assert data["rating"] == "Strong"
    assert data["question_id"] == "TECH_01"


def test_interview_evaluate_endpoint_empty_answer(client, synthetic_interview):
    question = synthetic_interview["technical_questions"][0]
    payload = {"question": question, "candidate_answer": "   "}
    response = client.post("/api/v1/interview/evaluate", json=payload)
    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()


# ============================================================================
# 8. HIRING REPORT GENERATOR (AGENT 7)
# ============================================================================
def test_hiring_report_endpoint_success(
    client,
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_summary,
    synthetic_report,
):
    from api.routes import reports

    monkeypatch.setattr(reports, "generate_hiring_report", lambda **kwargs: synthetic_report)

    payload = {
        "resume": synthetic_resume,
        "job_description": synthetic_jd,
        "match_result": synthetic_match,
        "skill_gap": synthetic_skill_gap,
        "interview_summary": synthetic_summary,
    }
    response = client.post("/api/v1/reports/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["report_title"] == "OptHire AI Hiring Report"
    assert data["final_decision"]["recommendation"] == "Hire"
    assert "disclaimer" in data


def test_hiring_report_endpoint_missing_journey_piece(client, synthetic_resume, synthetic_jd):
    # Missing match_result, skill_gap, interview_summary
    payload = {"resume": synthetic_resume, "job_description": synthetic_jd}
    response = client.post("/api/v1/reports/generate", json=payload)
    assert response.status_code == 422


# ============================================================================
# 9. PIPELINE ORCHESTRATION (AGENTS 1–5)
# ============================================================================
def test_pipeline_run_endpoint_success(
    client,
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_interview,
):
    from api.routes import pipeline

    expected_pipeline_output = {
        "status": "success",
        "resume": synthetic_resume,
        "job_description": synthetic_jd,
        "match_result": synthetic_match,
        "skill_gap": synthetic_skill_gap,
        "interview": synthetic_interview,
    }

    # Verify that the route invokes the existing HiringPipeline class
    class MockHiringPipeline:
        def __init__(self, output_directory=None):
            self.output_directory = output_directory

        def run(self, resume_path, job_description):
            assert resume_path.endswith(".pdf")
            assert "Senior Python Developer" in job_description
            return expected_pipeline_output

    monkeypatch.setattr(pipeline, "HiringPipeline", MockHiringPipeline)

    dummy_pdf = b"%PDF-1.4 dummy pdf bytes"
    files = {"file": ("candidate_resume.pdf", io.BytesIO(dummy_pdf), "application/pdf")}
    data = {"job_description": "Senior Python Developer with FastAPI and SQL experience."}

    response = client.post("/api/v1/pipeline/run", files=files, data=data)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert "resume" in result
    assert "interview" in result


def test_pipeline_run_endpoint_unsupported_file(client):
    files = {"file": ("test.png", io.BytesIO(b"dummy png"), "image/png")}
    data = {"job_description": "Valid job description text."}
    response = client.post("/api/v1/pipeline/run", files=files, data=data)
    assert response.status_code == 415


def test_pipeline_run_endpoint_empty_jd(client):
    dummy_pdf = b"%PDF-1.4 content"
    files = {"file": ("resume.pdf", io.BytesIO(dummy_pdf), "application/pdf")}
    data = {"job_description": "   "}
    response = client.post("/api/v1/pipeline/run", files=files, data=data)
    assert response.status_code == 400
    assert "Job description text cannot be empty" in response.json()["message"]


# ============================================================================
# 10. ERROR RESPONSE SCHEMA CONFORMANCE
# ============================================================================
def test_error_response_schema_conformance(client):
    from schemas.common import ErrorResponse

    # Test 422 validation error
    res_422 = client.post("/api/v1/jobs/parse", json={"job_description": "too short"})
    assert res_422.status_code == 422
    err_422 = ErrorResponse.model_validate(res_422.json())
    assert err_422.code == 422
    assert err_422.error == "VALIDATION_ERROR"

    # Test 400 client error
    res_400 = client.post("/api/v1/match", json={"resume": {}, "job_description": {}})
    assert res_400.status_code == 400
    err_400 = ErrorResponse.model_validate(res_400.json())
    assert err_400.code == 400
    assert err_400.error == "HTTP_ERROR"

