import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY

from agents.hiring_report.prompts import (
    hiring_report_prompt
)


os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


VALID_RECOMMENDATIONS = {
    "Strong Hire",
    "Hire",
    "Consider",
    "No Hire"
}


VALID_RISK_LEVELS = {
    "Low",
    "Medium",
    "High"
}


def clean_json_response(
    result: str
) -> str:
    """
    Removes markdown code fences if Gemini
    accidentally includes them.
    """

    result = result.strip()

    if result.startswith("```json"):
        result = result[7:]

    elif result.startswith("```"):
        result = result[3:]

    if result.endswith("```"):
        result = result[:-3]

    return result.strip()


def validate_score(
    score,
    score_name: str
):
    """
    Ensures a score is numeric and between 0 and 100.
    """

    if not isinstance(
        score,
        (int, float)
    ):
        raise ValueError(
            f"{score_name} must be a number."
        )

    if score < 0 or score > 100:
        raise ValueError(
            f"{score_name} must be between 0 and 100."
        )


def validate_hiring_report(
    report: dict
) -> None:
    """
    Performs basic validation on the final hiring report.
    """

    required_sections = [
        "candidate",
        "executive_summary",
        "scores",
        "resume_evaluation",
        "interview_evaluation",
        "skill_gap_evaluation",
        "hiring_risks",
        "key_reasons_to_hire",
        "key_reasons_for_caution",
        "final_decision"
    ]

    for section in required_sections:

        if section not in report:

            raise ValueError(
                f"Missing required report section: "
                f"{section}"
            )

    scores = report.get(
        "scores",
        {}
    )

    validate_score(
        scores.get(
            "resume_match_score"
        ),
        "resume_match_score"
    )

    validate_score(
        scores.get(
            "interview_score"
        ),
        "interview_score"
    )

    validate_score(
        scores.get(
            "final_hiring_score"
        ),
        "final_hiring_score"
    )

    validate_score(
        scores.get(
            "decision_confidence"
        ),
        "decision_confidence"
    )

    final_decision = report.get(
        "final_decision",
        {}
    )

    recommendation = final_decision.get(
        "recommendation"
    )

    if recommendation not in VALID_RECOMMENDATIONS:

        raise ValueError(
            "Invalid final recommendation: "
            f"{recommendation}"
        )

    risk_level = final_decision.get(
        "risk_level"
    )

    if risk_level not in VALID_RISK_LEVELS:

        raise ValueError(
            "Invalid risk level: "
            f"{risk_level}"
        )


def generate_hiring_report(
    resume: dict,
    job_description: dict,
    match_result: dict,
    skill_gap: dict,
    interview_summary: dict
) -> dict:
    """
    Generates the final OptHire AI hiring report.
    """

    prompt = hiring_report_prompt(
        resume=resume,
        job_description=job_description,
        match_result=match_result,
        skill_gap=skill_gap,
        interview_summary=interview_summary
    )

    response = llm.invoke(
        prompt
    )

    result = clean_json_response(
        response.content
    )

    try:

        report = json.loads(
            result
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Gemini returned invalid JSON "
            "for the final hiring report.\n\n"
            f"Response:\n{result}"
        ) from error

    validate_hiring_report(
        report
    )

    return report