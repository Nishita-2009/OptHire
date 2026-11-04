import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY
from agents.skill_gap.prompts import skill_gap_prompt

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


def analyze_skill_gap(resume_json, jd_json, match_result):

    prompt = skill_gap_prompt(
        resume_json,
        jd_json,
        match_result
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
            f"Invalid JSON returned by Gemini:\n\n{result}"
        )