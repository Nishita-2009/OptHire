import json


def hiring_report_prompt(
    resume: dict,
    job_description: dict,
    match_result: dict,
    skill_gap: dict,
    interview_summary: dict
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

    interview_json = json.dumps(
        interview_summary,
        indent=4,
        ensure_ascii=False
    )

    return f"""
You are a Senior Hiring Decision Analyst.

Your task is to generate the final hiring report for a candidate.

Carefully analyze:

1. Candidate Resume
2. Target Job Description
3. ATS Match Evaluation
4. Skill Gap Analysis
5. AI Interview Performance

Your report must be evidence-based, fair, concise, and useful to a recruiter.

IMPORTANT RULES:

1. Use only information available in the provided data.
2. Do not invent candidate experience, skills, qualifications, or achievements.
3. Do not use protected or irrelevant personal characteristics in the hiring decision.
4. Clearly separate resume-based evidence from interview-based evidence.
5. Consider both strengths and risks.
6. A high resume score must not automatically mean a strong interview result.
7. A strong interview must not erase major mandatory job requirement gaps.
8. If the interview was incomplete or provisional (with evaluated answers provided), report the partial interview score, clearly state that the interview is in progress, mention the number of answered questions vs total questions, and reduce decision confidence accordingly. Do NOT state that the interview was not conducted when evaluated answers or a provisional summary are provided. If the interview summary indicates 'Not Started', clearly report it as not started.
9. Return ONLY valid JSON.
10. Do not use markdown.
11. Do not use code fences.
12. The candidate name, target role, and company specified in the inputs are authoritative. You must populate candidate.name and candidate.target_role directly from them, and ensure all narrative sections (including candidate_summary, executive_summary, and resume_evaluation.summary) strictly reference the authoritative candidate name and target role, never substituting generic or alternative job titles.

Generate a final decision using one of:

- Strong Hire
- Hire
- Consider
- No Hire

Risk level must be one of:

- Low
- Medium
- High

Return exactly this JSON structure:

{{
    "report_title": "OptHire AI Hiring Report",

    "candidate": {{
        "name": "",
        "target_role": "",
        "candidate_summary": ""
    }},

    "executive_summary": "",

    "scores": {{
        "resume_match_score": 0,
        "interview_score": 0,
        "final_hiring_score": 0,
        "decision_confidence": 0
    }},

    "resume_evaluation": {{
        "matched_skills": [],
        "missing_skills": [],
        "key_strengths": [],
        "key_weaknesses": [],
        "summary": ""
    }},

    "interview_evaluation": {{
        "performance_level": "",
        "strongest_areas": [],
        "weakest_areas": [],
        "summary": ""
    }},

    "skill_gap_evaluation": {{
        "priority_gaps": [],
        "estimated_upskilling_time": "",
        "development_summary": ""
    }},

    "hiring_risks": [
        {{
            "risk": "",
            "severity": "",
            "reason": ""
        }}
    ],

    "key_reasons_to_hire": [],

    "key_reasons_for_caution": [],

    "final_decision": {{
        "recommendation": "",
        "risk_level": "",
        "reasoning": "",
        "next_action": ""
    }},

    "recruiter_notes": "",

    "disclaimer": "This AI-generated report is decision support only. Final hiring decisions should include appropriate human review."
}}

CANDIDATE RESUME:
{resume_json}

TARGET JOB DESCRIPTION:
{jd_json}

ATS MATCH RESULT:
{match_json}

SKILL GAP REPORT:
{skill_gap_json}

INTERVIEW SUMMARY:
{interview_json}
"""