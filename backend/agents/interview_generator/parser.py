import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY
from agents.interview_generator.prompts import interview_prompt


os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2
)


EXPECTED_COUNTS = {
    "technical_questions": 5,
    "coding_questions": 3,
    "resume_based_questions": 3,
    "project_based_questions": 3,
    "missing_skill_questions": 2,
    "behavioral_questions": 3,
    "hr_questions": 2,
}


def clean_json_response(result: str) -> str:
    """
    Removes markdown code fences if Gemini includes them.
    """

    result = result.strip()

    if result.startswith("```json"):
        result = result[7:]

    elif result.startswith("```"):
        result = result[3:]

    if result.endswith("```"):
        result = result[:-3]

    return result.strip()


def validate_interview(interview: dict) -> None:
    """
    Performs basic validation on the generated interview.
    """

    for category, expected_count in EXPECTED_COUNTS.items():

        if category not in interview:
            raise ValueError(
                f"Missing interview category: {category}"
            )

        questions = interview[category]

        if not isinstance(questions, list):
            raise ValueError(
                f"{category} must be a list."
            )

        if len(questions) != expected_count:
            raise ValueError(
                f"{category} should contain "
                f"{expected_count} questions, "
                f"but Gemini returned {len(questions)}."
            )

    all_question_ids = []

    for category in EXPECTED_COUNTS:

        for question in interview[category]:

            question_id = question.get("question_id")

            if not question_id:
                raise ValueError(
                    f"A question in {category} "
                    "does not have a question_id."
                )

            all_question_ids.append(question_id)

    if len(all_question_ids) != len(set(all_question_ids)):
        raise ValueError(
            "Duplicate question IDs found."
        )


def generate_interview(
    resume: dict,
    job_description: dict,
    match_result: dict,
    skill_gap: dict
) -> dict:
    """
    Generates a personalized 21-question interview.
    """

    prompt = interview_prompt(
        resume,
        job_description,
        match_result,
        skill_gap
    )

    response = llm.invoke(prompt)

    result = clean_json_response(
        response.content
    )

    try:
        interview = json.loads(result)

    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned invalid JSON.\n\n"
            f"Response:\n{result}"
        ) from error

    validate_interview(interview)

    return interview