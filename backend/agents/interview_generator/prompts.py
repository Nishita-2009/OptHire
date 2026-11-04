import json


def interview_prompt(
    resume: dict,
    job_description: dict,
    match_result: dict,
    skill_gap: dict
) -> str:

    resume_json = json.dumps(
        resume,
        indent=4,
        ensure_ascii=False
    )

    jd_json = json.dumps(
        job_description,
        indent=4,
        ensure_ascii=False
    )

    match_json = json.dumps(
        match_result,
        indent=4,
        ensure_ascii=False
    )

    skill_gap_json = json.dumps(
        skill_gap,
        indent=4,
        ensure_ascii=False
    )

    return f"""
You are a Senior Technical Interviewer and Recruitment Specialist.

Your task is to design a highly personalized interview for one candidate.

Carefully analyze:

1. The candidate's resume
2. The target job description
3. The ATS match evaluation
4. The candidate's skill gap report

The interview must be specific to this candidate and this job role.

Do not generate generic questions when candidate-specific questions can be asked.

Generate exactly:

- 5 technical questions
- 3 coding questions
- 3 resume-based questions
- 3 project-based questions
- 2 missing-skill questions
- 3 behavioral questions
- 2 HR questions

Total: 21 questions.

Difficulty should be adapted to:
- the candidate's experience,
- the job requirements,
- the ATS match score,
- and the candidate's strengths and weaknesses.

For every question, provide:
- a unique question_id,
- the question,
- difficulty,
- purpose,
- expected_answer_points,
- evaluation_criteria.

Rules:

1. Return ONLY valid JSON.
2. Do not use markdown.
3. Do not include ```json.
4. Do not include any explanation outside the JSON.
5. Difficulty must be one of:
   "Easy", "Medium", or "Hard".
6. question_id values must be unique.
7. Do not invent experience, projects, skills, or qualifications that are
   not supported by the provided data.
8. Missing-skill questions should test awareness and learning ability.
   Do not assume the candidate already has the missing skill.
9. The estimated interview duration should be realistic.
10. The interview strategy should briefly explain why this interview
    structure is appropriate for this candidate.

Return exactly this JSON structure:

{{
    "candidate_level": "",
    "target_role": "",
    "estimated_interview_duration": "",
    "overall_interview_difficulty": "",
    "interview_strategy": "",

    "question_distribution": {{
        "technical": 5,
        "coding": 3,
        "resume_based": 3,
        "project_based": 3,
        "missing_skill": 2,
        "behavioral": 3,
        "hr": 2,
        "total": 21
    }},

    "technical_questions": [
        {{
            "question_id": "TECH_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ],

    "coding_questions": [
        {{
            "question_id": "CODE_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ],

    "resume_based_questions": [
        {{
            "question_id": "RESUME_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ],

    "project_based_questions": [
        {{
            "question_id": "PROJECT_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ],

    "missing_skill_questions": [
        {{
            "question_id": "GAP_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ],

    "behavioral_questions": [
        {{
            "question_id": "BEHAVIOR_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ],

    "hr_questions": [
        {{
            "question_id": "HR_01",
            "question": "",
            "difficulty": "",
            "purpose": "",
            "expected_answer_points": [],
            "evaluation_criteria": []
        }}
    ]
}}

CANDIDATE RESUME:
{resume_json}

TARGET JOB DESCRIPTION:
{jd_json}

ATS MATCH RESULT:
{match_json}

SKILL GAP REPORT:
{skill_gap_json}
"""