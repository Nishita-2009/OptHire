"""
Gemini Service Abstraction Layer.
Provides a factory for ChatGoogleGenerativeAI instances and safe invocation
wrappers with bounded error handling.
"""
import os
from typing import Any, Optional, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from services.json_service import parse_json_safely


class GeminiService:
    """
    Factory and service wrapper for Google Gemini model operations.
    Maintains compatibility with existing OptHire agent configurations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = settings.GEMINI_MODEL,
        default_temperature: float = settings.DEFAULT_TEMPERATURE,
    ):
        self.api_key = api_key or settings.google_api_key
        self.default_model = default_model
        self.default_temperature = default_temperature

    def create_llm(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ChatGoogleGenerativeAI:
        """
        Creates and returns a new ChatGoogleGenerativeAI instance.
        """
        key = self.api_key
        if not key:
            raise ValueError(
                "Gemini API key is not configured. Please ensure GOOGLE_API_KEY is set."
            )
        os.environ["GOOGLE_API_KEY"] = key

        return ChatGoogleGenerativeAI(
            model=model or self.default_model,
            temperature=self.default_temperature if temperature is None else temperature,
        )

    def invoke_and_parse_json(
        self,
        prompt: str,
        llm: Optional[Any] = None,
        context: str = "Gemini Response",
    ) -> Union[dict, list]:
        """
        Invokes the LLM with the given prompt and parses the JSON response cleanly.
        Catches upstream errors and wraps them in a sanitized ValueError.
        """
        active_llm = llm or self.create_llm()
        try:
            response = active_llm.invoke(prompt)
            content = getattr(response, "content", "")
            return parse_json_safely(content, context=context)
        except ValueError:
            raise
        except Exception as exc:
            # Wrap upstream network/API exceptions into a clean runtime error
            raise RuntimeError(f"Upstream AI generation failed: {str(exc)}") from exc


# Shared singleton instance for API dependency injection
gemini_service = GeminiService()
