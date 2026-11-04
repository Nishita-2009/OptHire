"""
JSON Processing and Sanitization Service.
Centralizes clean markdown extraction and safe JSON deserialization.
"""
import json
from typing import Any, Union


def clean_json_markdown(raw_text: str) -> str:
    """
    Strips markdown code fences (```json ... ``` or ``` ... ```)
    from LLM responses.
    """
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def parse_json_safely(raw_text: str, context: str = "Response") -> Union[dict, list]:
    """
    Safely deserializes raw JSON text, cleaning any markdown fences first.
    Raises ValueError with a sanitized, safe message on failure.
    """
    cleaned = clean_json_markdown(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Provide a clean, truncated error message without disclosing sensitive candidate data
        sample = (cleaned[:120] + "...") if len(cleaned) > 120 else cleaned
        raise ValueError(f"Invalid JSON in {context}: {exc.msg} (Snippet: {sample!r})") from exc
