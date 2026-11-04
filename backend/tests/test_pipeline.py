"""
Test Suite: HiringPipeline Orchestration (Agents 1–5)
Verifies sequential pipeline execution, file saving, and output structure
using synthetic fixtures and mocked Gemini responses.
"""
import json
import pytest
from tests.conftest import MockLLM
from orchestrator.hiring_pipeline import HiringPipeline


def test_hiring_pipeline_mocked_run(
    tmp_path,
    monkeypatch,
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_interview,
):
    from agents.resume_parser import parser as a1
    from agents.jd_parser import parser as a2
    from agents.resume_matcher import parser as a3
    from agents.skill_gap import parser as a4
    from agents.interview_generator import parser as a5

    monkeypatch.setattr(a1, "llm", MockLLM(json.dumps(synthetic_resume)))
    monkeypatch.setattr(a2, "llm", MockLLM(json.dumps(synthetic_jd)))
    monkeypatch.setattr(a3, "llm", MockLLM(json.dumps(synthetic_match)))
    monkeypatch.setattr(a4, "llm", MockLLM(json.dumps(synthetic_skill_gap)))
    monkeypatch.setattr(a5, "llm", MockLLM(json.dumps(synthetic_interview)))

    out_dir = tmp_path / "test_outputs"
    pipeline = HiringPipeline(output_directory=str(out_dir))

    synthetic_pdf = "backend/uploads/sample_resume_synthetic.pdf"
    raw_jd = "Senior Python Developer with FastAPI and SQL experience."

    result = pipeline.run(
        resume_path=synthetic_pdf,
        job_description=raw_jd,
    )

    assert result["status"] == "success"
    assert "resume" in result
    assert "job_description" in result
    assert "match_result" in result
    assert "skill_gap" in result
    assert "interview" in result

    # Check files were written
    assert (out_dir / "parsed_resume.json").exists()
    assert (out_dir / "parsed_jd.json").exists()
    assert (out_dir / "match_result.json").exists()
    assert (out_dir / "skill_gap_report.json").exists()
    assert (out_dir / "interview_questions.json").exists()
