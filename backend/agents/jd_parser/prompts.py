def jd_parser_prompt(job_description: str):

    return f"""
You are an expert HR Job Description Parser.

Analyze the following Job Description.

Return ONLY valid JSON.

Extract:

- Job Title
- Required Skills
- Preferred Skills
- Experience
- Education
- Responsibilities
- Certifications
- Location
- Employment Type
- Salary (if available)
- Company Name (if available)

Return this JSON:

{{
    "company": "",
    "job_title": "",
    "experience": "",
    "education": "",

    "required_skills": [],

    "preferred_skills": [],

    "responsibilities": [],

    "certifications": [],

    "location": "",

    "employment_type": "",

    "salary": ""
}}

Job Description:

{job_description}
"""