"""
FastAPI Dependencies for OptHire API.
Provides dependency injection providers for services.
"""
from services.gemini_service import GeminiService, gemini_service


def get_gemini_service() -> GeminiService:
    """Dependency provider for GeminiService."""
    return gemini_service
