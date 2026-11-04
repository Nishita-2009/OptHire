"""
Test Suite: Agent Imports and Signatures Verification
Verifies that all 7 OptHire agents and orchestration modules import cleanly
and expose their required public entry points.
"""
import pytest


def test_agent_1_resume_parser_imports():
    from agents.resume_parser.parser import parse_resume
    from agents.resume_parser.pdf_reader import extract_resume_text
    from agents.resume_parser.prompts import resume_parser_prompt

    assert callable(parse_resume)
    assert callable(extract_resume_text)
    assert callable(resume_parser_prompt)


def test_agent_2_jd_parser_imports():
    from agents.jd_parser.parser import parse_job_description
    from agents.jd_parser.prompts import jd_parser_prompt

    assert callable(parse_job_description)
    assert callable(jd_parser_prompt)


def test_agent_3_resume_matcher_imports():
    from agents.resume_matcher.parser import match_resume
    from agents.resume_matcher.prompts import resume_match_prompt

    assert callable(match_resume)
    assert callable(resume_match_prompt)


def test_agent_4_skill_gap_imports():
    from agents.skill_gap.parser import analyze_skill_gap
    from agents.skill_gap.prompts import skill_gap_prompt

    assert callable(analyze_skill_gap)
    assert callable(skill_gap_prompt)


def test_agent_5_interview_generator_imports():
    from agents.interview_generator.parser import (
        generate_interview,
        validate_interview,
        clean_json_response,
    )
    from agents.interview_generator.prompts import interview_prompt

    assert callable(generate_interview)
    assert callable(validate_interview)
    assert callable(clean_json_response)
    assert callable(interview_prompt)


def test_agent_6_interview_evaluator_imports():
    from agents.interview_evaluator.evaluator import (
        evaluate_answer,
        generate_final_interview_summary,
        clean_json_response,
    )
    from agents.interview_evaluator.prompts import (
        answer_evaluation_prompt,
        final_interview_summary_prompt,
    )

    assert callable(evaluate_answer)
    assert callable(generate_final_interview_summary)
    assert callable(clean_json_response)
    assert callable(answer_evaluation_prompt)
    assert callable(final_interview_summary_prompt)


def test_agent_7_hiring_report_imports():
    from agents.hiring_report.generator import (
        generate_hiring_report,
        validate_hiring_report,
        validate_score,
        clean_json_response,
    )
    from agents.hiring_report.prompts import hiring_report_prompt

    assert callable(generate_hiring_report)
    assert callable(validate_hiring_report)
    assert callable(validate_score)
    assert callable(clean_json_response)
    assert callable(hiring_report_prompt)


def test_orchestration_pipeline_imports():
    from orchestrator.hiring_pipeline import HiringPipeline
    from workflows.hiring_pipeline import HiringPipeline as WorkflowPipeline

    assert callable(HiringPipeline)
    assert callable(WorkflowPipeline)
    pipeline = HiringPipeline()
    assert hasattr(pipeline, "run")
    assert hasattr(pipeline, "save_json")
