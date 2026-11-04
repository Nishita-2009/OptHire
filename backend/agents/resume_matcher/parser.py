import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY
from agents.resume_matcher.prompts import resume_match_prompt

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


def match_resume(resume_json, jd_json):

    prompt = resume_match_prompt(
        resume_json,
        jd_json
    )

    response = llm.invoke(prompt)

    result = response.content.strip()

    if result.startswith("```json"):
        result = result.replace("```json", "")
        result = result.replace("```", "").strip()

    try:
        return json.loads(result)

    except json.JSONDecodeError:

        raise ValueError(
            f"Invalid JSON received from Gemini:\n\n{result}"
        )