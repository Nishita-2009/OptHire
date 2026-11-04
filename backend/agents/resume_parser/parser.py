import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GOOGLE_API_KEY
from agents.resume_parser.prompts import resume_parser_prompt

# Set the Gemini API Key
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize the Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


def parse_resume(resume_text: str) -> dict:
    """
    Sends the resume text to Gemini and returns the parsed JSON.
    """

    # Create the prompt
    prompt = resume_parser_prompt(resume_text)

    # Get response from Gemini
    response = llm.invoke(prompt)

    result = response.content.strip()

    # Remove markdown formatting if Gemini returns ```json
    if result.startswith("```json"):
        result = result.replace("```json", "")
        result = result.replace("```", "").strip()

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        raise ValueError(
            "Gemini returned an invalid JSON response.\n\n"
            f"Response:\n{result}"
        )