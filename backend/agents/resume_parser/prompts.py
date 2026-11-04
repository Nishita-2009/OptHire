def resume_parser_prompt(resume_text: str):

    return f"""
You are an expert HR Resume Parsing AI.

Analyze the following resume and extract all possible information.

Return ONLY valid JSON.

Use this structure:

{{
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "summary": "",

    "education": [
        {{
            "degree": "",
            "college": "",
            "year": "",
            "cgpa": ""
        }}
    ],

    "experience": [
        {{
            "company": "",
            "role": "",
            "duration": "",
            "description": ""
        }}
    ],

    "skills": [],

    "projects": [
        {{
            "title": "",
            "description": "",
            "technologies": []
        }}
    ],

    "certifications": [],

    "languages": [],

    "achievements": []
}}

Resume:

{resume_text}
"""