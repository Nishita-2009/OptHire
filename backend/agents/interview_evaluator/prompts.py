import json


def answer_evaluation_prompt(
    question: dict,
    candidate_answer: str
) -> str:

    question_json = json.dumps(
        question,
        indent=4,
        ensure_ascii=False
    )

    return f"""
You are a Senior Technical Interview Evaluator.

Evaluate the candidate's answer to the interview question.

Use:
- the question,
- its purpose,
- expected answer points,
- evaluation criteria,
- and difficulty level.

Evaluate only what the candidate actually said.

Do not invent knowledge or experience that is not present in the answer.

Scoring rules:

- 90 to 100: Excellent
- 75 to 89: Strong
- 60 to 74: Acceptable
- 40 to 59: Weak
- 0 to 39: Poor

Return ONLY valid JSON.

Do not use markdown.
Do not use code fences.

Return exactly this structure:

{{
    "score": 0,
    "rating": "",
    "answer_summary": "",
    "strengths": [],
    "missing_points": [],
    "feedback": "",
    "ideal_answer": ""
}}

INTERVIEW QUESTION:

{question_json}

CANDIDATE ANSWER:

{candidate_answer}
"""

def final_interview_summary_prompt(
    evaluations: list
) -> str:

    evaluations_json = json.dumps(
        evaluations,
        indent=4,
        ensure_ascii=False
    )

    return f"""
You are a Senior Hiring Manager.

Analyze the complete interview evaluation results.

Create a final interview performance summary.

Base the decision only on the provided evaluation results.

Return ONLY valid JSON.

Do not use markdown.
Do not use code fences.

Return exactly this structure:

{{
    "overall_interview_score": 0,

    "performance_level": "",

    "technical_performance": "",

    "problem_solving_performance": "",

    "communication_performance": "",

    "strongest_areas": [],

    "weakest_areas": [],

    "key_strengths": [],

    "areas_for_improvement": [],

    "interview_summary": "",

    "recommendation": "",

    "next_action": ""
}}

Recommendation must be one of:

- Strong Hire
- Hire
- Consider
- No Hire

COMPLETE INTERVIEW EVALUATIONS:

{evaluations_json}
"""