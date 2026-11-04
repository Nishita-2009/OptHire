"""
Test Suite: Agent Prompts Verification
Verifies that all prompt generator functions produce expected formatting,
valid structures, and fairness guidelines.
"""
from agents.resume_parser.prompts import resume_parser_prompt
from agents.jd_parser.prompts import jd_parser_prompt
from agents.resume_matcher.prompts import resume_match_prompt
from agents.skill_gap.prompts import skill_gap_prompt
from agents.interview_generator.prompts import interview_prompt
from agents.interview_evaluator.prompts import (
    answer_evaluation_prompt,
    final_interview_summary_prompt,
)
from agents.hiring_report.prompts import hiring_report_prompt


def test_agent_1_prompt_generation():
    prompt = resume_parser_prompt("Sample Resume Text for Testing")
    assert "You are an expert HR Resume Parsing AI." in prompt
    assert "Sample Resume Text for Testing" in prompt
    assert '"skills": []' in prompt
    assert '"education": [' in prompt


def test_agent_2_prompt_generation():
    prompt = jd_parser_prompt("Looking for Senior Python Engineer")
    assert "You are an expert HR Job Description Parser." in prompt
    assert "Looking for Senior Python Engineer" in prompt
    assert '"required_skills": []' in prompt
    assert '"job_title": ""' in prompt


def test_agent_3_prompt_generation(synthetic_resume, synthetic_jd):
    prompt = resume_match_prompt(synthetic_resume, synthetic_jd)
    assert "You are an Expert ATS Resume Evaluation AI." in prompt
    assert "overall_match_score" in prompt
    assert "matched_skills" in prompt
    assert "missing_skills" in prompt
    assert "Alex Morgan" in prompt


def test_agent_4_prompt_generation(synthetic_resume, synthetic_jd, synthetic_match):
    prompt = skill_gap_prompt(synthetic_resume, synthetic_jd, synthetic_match)
    assert "You are an AI Career Growth Advisor." in prompt
    assert "overall_gap_summary" in prompt
    assert "missing_skills" in prompt
    assert "recommended_projects" in prompt


def test_agent_5_prompt_generation(synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap):
    prompt = interview_prompt(synthetic_resume, synthetic_jd, synthetic_match, synthetic_skill_gap)
    assert "You are a Senior Technical Interviewer and Recruitment Specialist." in prompt
    assert "Total: 21 questions." in prompt
    assert "5 technical questions" in prompt
    assert "3 coding questions" in prompt
    assert "3 resume-based questions" in prompt
    assert "3 project-based questions" in prompt
    assert "2 missing-skill questions" in prompt
    assert "3 behavioral questions" in prompt
    assert "2 HR questions" in prompt


def test_agent_6_prompts_generation(synthetic_interview, synthetic_evaluations):
    first_question = synthetic_interview["technical_questions"][0]
    eval_prompt = answer_evaluation_prompt(first_question, "My answer to technical question.")
    assert "You are a Senior Technical Interview Evaluator." in prompt_or_str(eval_prompt)
    assert "My answer to technical question." in eval_prompt
    assert "ideal_answer" in eval_prompt

    summary_prompt = final_interview_summary_prompt(synthetic_evaluations)
    assert "You are a Senior Hiring Manager." in summary_prompt
    assert "overall_interview_score" in summary_prompt


def test_agent_7_prompt_generation(
    synthetic_resume,
    synthetic_jd,
    synthetic_match,
    synthetic_skill_gap,
    synthetic_summary,
):
    prompt = hiring_report_prompt(
        synthetic_resume,
        synthetic_jd,
        synthetic_match,
        synthetic_skill_gap,
        synthetic_summary,
    )
    assert "You are a Senior Hiring Decision Analyst." in prompt
    assert "Do not use protected or irrelevant personal characteristics in the hiring decision." in prompt
    assert "This AI-generated report is decision support only." in prompt
    assert "final_decision" in prompt


def prompt_or_str(val):
    return str(val)
