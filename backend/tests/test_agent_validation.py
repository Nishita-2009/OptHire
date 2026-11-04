"""
Test Suite: Agent Execution & Validation with Mocked Gemini Responses
Validates all 7 agents end-to-end without consuming real Gemini API quota.
Tests JSON parsing, markdown stripping, schema validation, error handling, and constraints.
"""
import copy
import json
import pytest
from tests.conftest import MockLLM


# ==========================================
# AGENT 1: RESUME PARSER
# ==========================================
def test_agent_1_parse_resume_success(monkeypatch, synthetic_resume):
    from agents.resume_parser import parser

    mock_json = json.dumps(synthetic_resume)
    monkeypatch.setattr(parser, "llm", MockLLM(mock_json))

    result = parser.parse_resume("Resume content here...")
    assert result["name"] == "Alex Morgan"
    assert "Python" in result["skills"]
    assert len(result["education"]) > 0


def test_agent_1_parse_resume_with_markdown_fences(monkeypatch, synthetic_resume):
    from agents.resume_parser import parser

    mock_fenced = f"```json\n{json.dumps(synthetic_resume)}\n```"
    monkeypatch.setattr(parser, "llm", MockLLM(mock_fenced))

    result = parser.parse_resume("Resume text...")
    assert result["name"] == "Alex Morgan"


def test_agent_1_parse_resume_invalid_json(monkeypatch):
    from agents.resume_parser import parser

    monkeypatch.setattr(parser, "llm", MockLLM("NOT VALID JSON"))
    with pytest.raises(ValueError, match="Gemini returned an invalid JSON response"):
        parser.parse_resume("Resume text...")


# ==========================================
# AGENT 2: JOB DESCRIPTION PARSER
# ==========================================
def test_agent_2_parse_jd_success(monkeypatch, synthetic_jd):
    from agents.jd_parser import parser

    mock_json = json.dumps(synthetic_jd)
    monkeypatch.setattr(parser, "llm", MockLLM(mock_json))

    result = parser.parse_job_description("Job description content...")
    assert result["job_title"] == "Software Engineer (Backend)"
    assert "Python" in result["required_skills"]


def test_agent_2_parse_jd_with_markdown_fences(monkeypatch, synthetic_jd):
    from agents.jd_parser import parser

    mock_fenced = f"```json\n{json.dumps(synthetic_jd)}\n```"
    monkeypatch.setattr(parser, "llm", MockLLM(mock_fenced))

    result = parser.parse_job_description("Job description...")
    assert result["company"] == "TechGlobal Innovations"


def test_agent_2_parse_jd_invalid_json(monkeypatch):
    from agents.jd_parser import parser

    monkeypatch.setattr(parser, "llm", MockLLM("Non-JSON output"))
    with pytest.raises(ValueError, match="Invalid JSON returned by Gemini"):
        parser.parse_job_description("Job description...")


# ==========================================
# AGENT 3: RESUME MATCHER
# ==========================================
def test_agent_3_match_resume_success(monkeypatch, synthetic_resume, synthetic_jd, synthetic_match):
    from agents.resume_matcher import parser

    mock_json = json.dumps(synthetic_match)
    monkeypatch.setattr(parser, "llm", MockLLM(mock_json))

    result = parser.match_resume(synthetic_resume, synthetic_jd)
    assert result["overall_match_score"] == 88
    assert "FastAPI" in result["matched_skills"]
    assert "Kubernetes" in result["missing_skills"]


def test_agent_3_match_resume_invalid_json(monkeypatch, synthetic_resume, synthetic_jd):
    from agents.resume_matcher import parser

    monkeypatch.setattr(parser, "llm", MockLLM("Invalid output"))
    with pytest.raises(ValueError, match="Invalid JSON received from Gemini"):
        parser.match_resume(synthetic_resume, synthetic_jd)


# ==========================================
# AGENT 4: SKILL GAP ANALYZER
# ==========================================
def test_agent_4_skill_gap_success(monkeypatch, synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap):
    from agents.skill_gap import parser

    mock_json = json.dumps(synthetic_skill_gap)
    monkeypatch.setattr(parser, "llm", MockLLM(mock_json))

    result = parser.analyze_skill_gap(synthetic_resume, synthetic_jd, synthetic_match)
    assert len(result["missing_skills"]) > 0
    assert result["missing_skills"][0]["skill"] == "Kubernetes"
    assert "CKAD" in result["recommended_certifications"][0]


def test_agent_4_skill_gap_invalid_json(monkeypatch, synthetic_resume, synthetic_jd, synthetic_match):
    from agents.skill_gap import parser

    monkeypatch.setattr(parser, "llm", MockLLM("{ broken json"))
    with pytest.raises(ValueError, match="Invalid JSON returned by Gemini"):
        parser.analyze_skill_gap(synthetic_resume, synthetic_jd, synthetic_match)


# ==========================================
# AGENT 5: INTERVIEW GENERATOR
# ==========================================
def test_agent_5_generate_interview_success(
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_interview,
):
    from agents.interview_generator import parser

    mock_json = json.dumps(synthetic_interview)
    monkeypatch.setattr(parser, "llm", MockLLM(mock_json))

    result = parser.generate_interview(
        synthetic_resume,
        synthetic_jd,
        synthetic_match,
        synthetic_skill_gap,
    )
    assert result["question_distribution"]["total"] == 21
    assert len(result["technical_questions"]) == 5
    assert len(result["coding_questions"]) == 3
    assert len(result["resume_based_questions"]) == 3
    assert len(result["project_based_questions"]) == 3
    assert len(result["missing_skill_questions"]) == 2
    assert len(result["behavioral_questions"]) == 3
    assert len(result["hr_questions"]) == 2


def test_agent_5_generate_interview_count_mismatch(
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_interview,
):
    from agents.interview_generator import parser

    bad_data = copy.deepcopy(synthetic_interview)
    bad_data["technical_questions"].pop()
    monkeypatch.setattr(parser, "llm", MockLLM(json.dumps(bad_data)))

    with pytest.raises(ValueError, match="technical_questions should contain 5 questions"):
        parser.generate_interview(
            synthetic_resume,
            synthetic_jd,
            synthetic_match,
            synthetic_skill_gap,
        )


def test_agent_5_generate_interview_duplicate_question_id(
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_interview,
):
    from agents.interview_generator import parser

    bad_data = copy.deepcopy(synthetic_interview)
    bad_data["technical_questions"][1]["question_id"] = "TECH_01"
    monkeypatch.setattr(parser, "llm", MockLLM(json.dumps(bad_data)))

    with pytest.raises(ValueError, match="Duplicate question IDs found"):
        parser.generate_interview(
            synthetic_resume,
            synthetic_jd,
            synthetic_match,
            synthetic_skill_gap,
        )


# ==========================================
# AGENT 6: INTERVIEW EVALUATOR
# ==========================================
def test_agent_6_evaluate_single_answer(monkeypatch, synthetic_interview):
    from agents.interview_evaluator import evaluator

    first_q = synthetic_interview["technical_questions"][0]
    mock_eval = {
        "score": 95,
        "rating": "Excellent",
        "answer_summary": "Accurate and clear explanation of async concurrency.",
        "strengths": ["Clear understanding of ASGI event loop"],
        "missing_points": [],
        "feedback": "Outstanding answer.",
        "ideal_answer": "In FastAPI, async endpoints leverage asyncio event loop...",
    }

    monkeypatch.setattr(evaluator, "llm", MockLLM(json.dumps(mock_eval)))

    result = evaluator.evaluate_answer(first_q, "Async functions use non-blocking event loops.")
    assert result["score"] == 95
    assert result["rating"] == "Excellent"
    assert result["question_id"] == "TECH_01"
    assert result["candidate_answer"] == "Async functions use non-blocking event loops."


def test_agent_6_generate_final_summary(monkeypatch, synthetic_evaluations, synthetic_summary):
    from agents.interview_evaluator import evaluator

    monkeypatch.setattr(evaluator, "llm", MockLLM(json.dumps(synthetic_summary)))

    result = evaluator.generate_final_interview_summary(synthetic_evaluations)
    assert result["overall_interview_score"] == 90
    assert result["performance_level"] == "Strong"
    assert result["recommendation"] == "Hire"


def test_agent_6_evaluate_answer_invalid_json(monkeypatch, synthetic_interview):
    from agents.interview_evaluator import evaluator

    first_q = synthetic_interview["technical_questions"][0]
    monkeypatch.setattr(evaluator, "llm", MockLLM("broken json string"))

    with pytest.raises(ValueError, match="Gemini returned invalid JSON while evaluating the answer"):
        evaluator.evaluate_answer(first_q, "Sample candidate answer")


# ==========================================
# AGENT 7: HIRING REPORT GENERATOR
# ==========================================
def test_agent_7_generate_hiring_report_success(
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_summary,
    synthetic_report,
):
    from agents.hiring_report import generator

    monkeypatch.setattr(generator, "llm", MockLLM(json.dumps(synthetic_report)))

    report = generator.generate_hiring_report(
        resume=synthetic_resume,
        job_description=synthetic_jd,
        match_result=synthetic_match,
        skill_gap=synthetic_skill_gap,
        interview_summary=synthetic_summary,
    )

    assert report["report_title"] == "OptHire AI Hiring Report"
    assert report["scores"]["final_hiring_score"] == 89
    assert report["final_decision"]["recommendation"] in generator.VALID_RECOMMENDATIONS
    assert report["final_decision"]["risk_level"] in generator.VALID_RISK_LEVELS
    assert "disclaimer" in report


def test_agent_7_validate_hiring_report_invalid_score(synthetic_report):
    from agents.hiring_report import generator

    bad_report = copy.deepcopy(synthetic_report)
    bad_report["scores"]["resume_match_score"] = 150  # Over 100

    with pytest.raises(ValueError, match="resume_match_score must be between 0 and 100"):
        generator.validate_hiring_report(bad_report)


def test_agent_7_validate_hiring_report_missing_section(synthetic_report):
    from agents.hiring_report import generator

    bad_report = copy.deepcopy(synthetic_report)
    del bad_report["executive_summary"]

    with pytest.raises(ValueError, match="Missing required report section: executive_summary"):
        generator.validate_hiring_report(bad_report)


def test_agent_7_validate_hiring_report_invalid_recommendation(synthetic_report):
    from agents.hiring_report import generator

    bad_report = copy.deepcopy(synthetic_report)
    bad_report["final_decision"]["recommendation"] = "InstaHire"  # Invalid

    with pytest.raises(ValueError, match="Invalid final recommendation"):
        generator.validate_hiring_report(bad_report)
