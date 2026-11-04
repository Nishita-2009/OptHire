import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY
from agents.jd_parser.prompts import jd_parser_prompt

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


def parse_job_description(job_description: str):

    prompt = jd_parser_prompt(job_description)

    response = llm.invoke(prompt)

    result = response.content.strip()

    if result.startswith("```json"):
        result = result.replace("```json", "")
        result = result.replace("```", "").strip()

    try:
        return json.loads(result)

    except json.JSONDecodeError:

        raise ValueError(
            "Invalid JSON returned by Gemini."
        )