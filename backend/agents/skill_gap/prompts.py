import json


def skill_gap_prompt(resume: dict, job_description: dict, match_result: dict):

    resume_json = json.dumps(resume, indent=4)

    jd_json = json.dumps(job_description, indent=4)

    match_json = json.dumps(match_result, indent=4)

    return f"""
You are an AI Career Growth Advisor.

Analyze:

1. Resume
2. Job Description
3. ATS Match Result

Your goal is to help the candidate become a stronger applicant.

Return ONLY valid JSON.

Return this format:

{{
    "overall_gap_summary": "",

    "missing_skills": [
        {{
            "skill": "",
            "priority": "",
            "reason": "",
            "estimated_learning_time": "",
            "expected_score_improvement": ""
        }}
    ],

    "recommended_projects": [],

    "recommended_certifications": [],

    "learning_resources": [
        {{
            "skill": "",
            "resource": "",
            "type": ""
        }}
    ],

    "career_advice": "",

    "estimated_total_learning_time": ""
}}

Resume:

{resume_json}

Job Description:

{jd_json}

Match Result:

{match_json}
"""