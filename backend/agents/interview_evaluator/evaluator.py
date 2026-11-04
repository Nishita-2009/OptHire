import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY

from agents.interview_evaluator.prompts import (
    answer_evaluation_prompt,
    final_interview_summary_prompt
)


os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


def clean_json_response(result: str) -> str:

    result = result.strip()

    if result.startswith("```json"):
        result = result[7:]

    elif result.startswith("```"):
        result = result[3:]

    if result.endswith("```"):
        result = result[:-3]

    return result.strip()


def evaluate_answer(
    question: dict,
    candidate_answer: str
) -> dict:

    prompt = answer_evaluation_prompt(
        question,
        candidate_answer
    )

    response = llm.invoke(prompt)

    result = clean_json_response(
        response.content
    )

    try:
        evaluation = json.loads(result)

    except json.JSONDecodeError as error:

        raise ValueError(
            "Gemini returned invalid JSON "
            "while evaluating the answer.\n\n"
            f"Response:\n{result}"
        ) from error

    evaluation["question_id"] = question.get(
        "question_id",
        ""
    )

    evaluation["question"] = question.get(
        "question",
        ""
    )

    evaluation["candidate_answer"] = (
        candidate_answer
    )

    evaluation["category"] = question.get(
        "category",
        ""
    )

    return evaluation


def generate_final_interview_summary(
    evaluations: list
) -> dict:

    prompt = final_interview_summary_prompt(
        evaluations
    )

    response = llm.invoke(prompt)

    result = clean_json_response(
        response.content
    )

    try:
        return json.loads(result)

    except json.JSONDecodeError as error:

        raise ValueError(
            "Gemini returned invalid JSON "
            "for the final interview summary.\n\n"
            f"Response:\n{result}"
        ) from error