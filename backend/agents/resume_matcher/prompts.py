import json


def resume_match_prompt(resume: dict, job_description: dict):

    resume_json = json.dumps(resume, indent=4)

    jd_json = json.dumps(job_description, indent=4)

    return f"""
You are an Expert ATS Resume Evaluation AI.

Your task is to compare the Resume JSON with the Job Description JSON.

Think like a Senior HR Manager.

Evaluate the candidate fairly.

Return ONLY valid JSON.

Evaluation Rules:

1. Calculate Overall Match Score (0-100)
2. Calculate Skill Match Score
3. Calculate Experience Match Score
4. Calculate Education Match Score
5. Explain every score.
6. Find all matching skills.
7. Find all missing skills.
8. Mention candidate strengths.
9. Mention candidate weaknesses.
10. Estimate interview difficulty.
11. Estimate confidence score.
12. Decide whether the recruiter should continue.

Return ONLY this JSON:

{{
    "overall_match_score": 0,

    "confidence_score": 0,

    "candidate_summary": "",

    "skill_match": {{
        "score": 0,
        "reason": ""
    }},

    "experience_match": {{
        "score": 0,
        "reason": ""
    }},

    "education_match": {{
        "score": 0,
        "reason": ""
    }},

    "matched_skills": [],

    "missing_skills": [],

    "strengths": [],

    "weaknesses": [],

    "risk_level": "",

    "salary_fit": "",

    "interview_difficulty": "",

    "recommendation": "",

    "next_action": ""
}}

Resume:

{resume_json}

Job Description:

{jd_json}
"""