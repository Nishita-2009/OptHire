"""
Frontend-Backend Integration Verification Tests (Phase 4.1).
Explicitly verifies all 14 frontend workflows matching the exact routes, payloads,
and response contracts used by frontend/src/services/api.js and UI components.
"""
import io
import json
import pytest
from tests.conftest import MockLLM, MockAIMessage
from agents.resume_parser import parser as rp_parser
from agents.jd_parser import parser as jd_parser
from agents.resume_matcher import parser as rm_parser
from agents.skill_gap import parser as sg_parser
from agents.interview_generator import parser as ig_parser
from agents.interview_evaluator import evaluator as ie_evaluator
from agents.hiring_report import generator as hr_generator


def test_workflow_01_backend_health(test_client):
    """Workflow 1: Backend health status check."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "healthy")
    assert "app" in data
    assert "version" in data


def test_workflow_02_candidate_registration(test_client):
    """Workflow 2: Candidate registration via POST /api/v1/candidates."""
    payload = {
        "full_name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "phone": "+1-555-0199",
        "resume_text": "Experienced Python Software Engineer with 4 years in FastAPI and cloud deployments.",
        "parsed_resume_data": {
            "name": "Jordan Lee",
            "skills": ["Python", "FastAPI", "Docker", "SQLAlchemy"],
            "experience": "4 years",
            "education": "B.S. in Computer Science",
            "projects": ["OptHire SaaS Backend"],
        },
    }
    resp = test_client.post("/api/v1/candidates", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["full_name"] == "Jordan Lee"
    assert data["email"] == "jordan.lee@example.com"
    assert data["parsed_resume_data"]["name"] == "Jordan Lee"


def test_workflow_03_candidate_listing_and_details(test_client):
    """Workflow 3: Candidate listing, single candidate details, and candidate analyses history."""
    # Create candidate
    create_resp = test_client.post(
        "/api/v1/candidates",
        json={"full_name": "Taylor Swift", "email": "taylor@music.com"},
    )
    assert create_resp.status_code == 201
    cand_id = create_resp.json()["id"]

    # 1. List candidates
    list_resp = test_client.get("/api/v1/candidates?skip=0&limit=50")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(c["id"] == cand_id for c in list_data["candidates"])

    # 2. Get candidate by ID
    get_resp = test_client.get(f"/api/v1/candidates/{cand_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["full_name"] == "Taylor Swift"

    # 3. Get candidate analysis history (verified route: /analysis singular)
    analysis_resp = test_client.get(f"/api/v1/candidates/{cand_id}/analysis")
    assert analysis_resp.status_code == 200
    assert "runs" in analysis_resp.json()
    assert analysis_resp.json()["total"] == 0


def test_workflow_04_resume_pdf_upload(test_client, monkeypatch, synthetic_resume):
    """Workflow 4: Resume PDF upload and Agent 1 extraction via POST /api/v1/resumes/parse."""
    from api.routes import resumes

    monkeypatch.setattr(resumes, "parse_resume", lambda text: synthetic_resume)
    monkeypatch.setattr(resumes, "extract_text_from_upload", lambda f: "Extracted candidate text")

    dummy_pdf = b"%PDF-1.4 synthetic candidate resume bytes"
    files = {"file": ("resume.pdf", io.BytesIO(dummy_pdf), "application/pdf")}

    resp = test_client.post("/api/v1/resumes/parse", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alex Morgan"
    assert "Python" in data["skills"]


def test_workflow_05_job_creation(test_client):
    """Workflow 5: Job creation via POST /api/v1/jobs."""
    payload = {
        "title": "Senior Backend Architect",
        "company": "Apex Technologies",
        "description": "Seeking an expert in Python, microservices, and distributed architecture.",
        "parsed_job_data": {
            "job_title": "Senior Backend Architect",
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_level": "Senior",
        },
    }
    resp = test_client.post("/api/v1/jobs", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["title"] == "Senior Backend Architect"
    assert data["company"] == "Apex Technologies"


def test_workflow_06_job_listing_and_details(test_client):
    """Workflow 6: Job listing and retrieval by UUID."""
    create_resp = test_client.post(
        "/api/v1/jobs",
        json={"title": "DevOps Engineer", "company": "Cloud Corp", "description": "Kubernetes and CI/CD specialist"},
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    # 1. List jobs
    list_resp = test_client.get("/api/v1/jobs?skip=0&limit=50")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert any(j["id"] == job_id for j in data["jobs"])

    # 2. Get job by ID
    get_resp = test_client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "DevOps Engineer"


def test_workflow_07_job_description_parsing(test_client, monkeypatch, synthetic_jd):
    """Workflow 7: JD parsing via Agent 2 (POST /api/v1/jobs/parse)."""
    monkeypatch.setattr(jd_parser, "llm", MockLLM(json.dumps(synthetic_jd)))

    resp = test_client.post(
        "/api/v1/jobs/parse",
        json={"job_description": "We are seeking a Python developer with FastAPI expertise."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_title"] == synthetic_jd["job_title"]
    assert "Python" in data["required_skills"]


def test_workflow_08_candidate_job_analysis(
    test_client, monkeypatch, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap
):
    """Workflow 8: Candidate-job analysis triggering Agents 3 & 4 via POST /api/v1/analysis."""
    # Create candidate and job
    cand_resp = test_client.post(
        "/api/v1/candidates",
        json={"full_name": "Sam Carter", "parsed_resume_data": synthetic_resume},
    )
    job_resp = test_client.post(
        "/api/v1/jobs",
        json={"title": "Software Engineer (Backend)", "company": "TechStart", "description": "Python job", "parsed_job_data": synthetic_jd},
    )
    cand_id = cand_resp.json()["id"]
    job_id = job_resp.json()["id"]

    # Mock Agents 3 & 4
    monkeypatch.setattr(rm_parser, "llm", MockLLM(json.dumps(synthetic_match)))
    monkeypatch.setattr(sg_parser, "llm", MockLLM(json.dumps(synthetic_skill_gap)))

    # Trigger analysis
    resp = test_client.post("/api/v1/analysis", json={"candidate_id": cand_id, "job_id": job_id})
    assert resp.status_code == 201
    analysis_data = resp.json()
    assert analysis_data["id"] is not None
    assert analysis_data["status"] == "completed"
    assert analysis_data["match_result"]["overall_match_score"] == synthetic_match["overall_match_score"]

    # Retrieve analysis
    get_resp = test_client.get(f"/api/v1/analysis/{analysis_data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == analysis_data["id"]


def test_workflows_09_to_14_full_interview_and_report_lifecycle(
    test_client, monkeypatch, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap, synthetic_interview, synthetic_evaluations, synthetic_summary, synthetic_report
):
    """
    Workflows 9 to 14:
    9. Interview session creation (Agent 5)
    10. Question retrieval (/questions)
    11. Answer submission and evaluation (Agent 6)
    12. Interview completion (/complete)
    13. Hiring report generation (Agent 7 - provisional & completed)
    14. Report retrieval (/reports/{id} and /analysis/{id}/report)
    """
    # Setup candidate, job, and analysis run
    cand_resp = test_client.post(
        "/api/v1/candidates",
        json={"full_name": "Robin Sterling", "parsed_resume_data": synthetic_resume},
    )
    job_resp = test_client.post(
        "/api/v1/jobs",
        json={"title": "Software Engineer (Backend)", "company": "ScaleUp Inc", "description": "FastAPI engineer", "parsed_job_data": synthetic_jd},
    )
    cand_id = cand_resp.json()["id"]
    job_id = job_resp.json()["id"]

    # Mock Matcher & Skill Gap for Analysis
    monkeypatch.setattr(rm_parser, "llm", MockLLM(json.dumps(synthetic_match)))
    monkeypatch.setattr(sg_parser, "llm", MockLLM(json.dumps(synthetic_skill_gap)))
    analysis_resp = test_client.post("/api/v1/analysis", json={"candidate_id": cand_id, "job_id": job_id})
    analysis_id = analysis_resp.json()["id"]

    # 9. Interview session creation (Agent 5)
    monkeypatch.setattr(ig_parser, "llm", MockLLM(json.dumps(synthetic_interview)))
    session_resp = test_client.post(
        "/api/v1/interviews",
        json={
            "candidate_id": cand_id,
            "job_id": job_id,
            "analysis_run_id": analysis_id,
            "generate_questions": True,
        },
    )
    assert session_resp.status_code == 201
    session_data = session_resp.json()
    session_id = session_data["session_id"]
    assert session_data["status"] == "in_progress"
    assert session_data["total_questions"] == 21

    # 10. Question retrieval
    q_resp = test_client.get(f"/api/v1/interviews/{session_id}/questions")
    assert q_resp.status_code == 200
    questions = q_resp.json()
    assert len(questions) == 21
    q1 = questions[0]
    assert q1["id"] is not None
    assert q1["is_answered"] is False

    # 11. Answer submission and evaluation (Agent 6)
    single_eval = synthetic_evaluations[0]
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps(single_eval)))
    ans_resp = test_client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"question_id": q1["id"], "answer": "In Python, list comprehensions provide a concise way to create lists."},
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert ans_data["score"] == single_eval["score"]
    assert ans_data["evaluation_result"] is not None
    assert ans_data["evaluation_result"]["rating"] == single_eval["rating"]

    # Verify answers retrieval
    ans_list_resp = test_client.get(f"/api/v1/interviews/{session_id}/answers")
    assert ans_list_resp.status_code == 200
    assert len(ans_list_resp.json()) == 1

    # 13a. Generate Provisional Hiring Report (with in-progress session)
    monkeypatch.setattr(hr_generator, "llm", MockLLM(json.dumps(synthetic_report)))
    prov_resp = test_client.post(
        "/api/v1/reports",
        json={"analysis_run_id": analysis_id, "interview_session_id": session_id},
    )
    assert prov_resp.status_code == 201
    prov_data = prov_resp.json()
    assert prov_data["is_provisional"] is True
    assert prov_data["overall_score"] is not None
    # Authoritative metadata verified
    assert prov_data["report_data"]["candidate"]["name"] == "Robin Sterling"
    assert prov_data["report_data"]["candidate"]["target_role"] == "Software Engineer (Backend)"

    # 12. Interview completion (Agent 6 final summary via /complete)
    monkeypatch.setattr(ie_evaluator, "llm", MockLLM(json.dumps(synthetic_summary)))
    complete_resp = test_client.post(f"/api/v1/interviews/{session_id}/complete")
    assert complete_resp.status_code == 200
    complete_data = complete_resp.json()
    assert complete_data["status"] == "completed"
    assert complete_data["final_summary"] is not None

    # 13b. Generate Final Completed Hiring Report
    final_rep_resp = test_client.post(
        "/api/v1/reports",
        json={"analysis_run_id": analysis_id, "interview_session_id": session_id},
    )
    assert final_rep_resp.status_code == 201
    final_rep = final_rep_resp.json()
    assert final_rep["is_provisional"] is False
    assert final_rep["report_data"]["candidate"]["name"] == "Robin Sterling"
    assert final_rep["report_data"]["candidate"]["target_role"] == "Software Engineer (Backend)"
    report_id = final_rep["id"]

    # 14. Report retrieval (both by report ID and analysis ID)
    get_rep = test_client.get(f"/api/v1/reports/{report_id}")
    assert get_rep.status_code == 200
    assert get_rep.json()["id"] == report_id

    get_analysis_rep = test_client.get(f"/api/v1/analysis/{analysis_id}/report")
    assert get_analysis_rep.status_code == 200
    assert get_analysis_rep.json()["id"] in (prov_data["id"], report_id)
    assert get_analysis_rep.json()["analysis_run_id"] == analysis_id
