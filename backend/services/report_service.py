"""
Report Service.
Provides high-level helpers for hiring report generation and validation.
"""
from typing import Any, Dict
from agents.hiring_report.generator import generate_hiring_report, validate_hiring_report


def build_hiring_report(
    resume: Dict[str, Any],
    job_description: Dict[str, Any],
    match_result: Dict[str, Any],
    skill_gap: Dict[str, Any],
    interview_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Coordinates Agent 7 report generation and returns validated report dictionary.
    """
    return generate_hiring_report(
        resume=resume,
        job_description=job_description,
        match_result=match_result,
        skill_gap=skill_gap,
        interview_summary=interview_summary,
    )

