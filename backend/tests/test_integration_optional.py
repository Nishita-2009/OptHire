"""
Optional Integration Tests for OptHire Live Gemini API Connection.
Protected by an environment flag: OPTHIRE_RUN_LIVE_TESTS=1.
By default, these tests are skipped so routine test runs consume zero paid API quota.
"""
import os
import pytest


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("OPTHIRE_RUN_LIVE_TESTS") != "1",
    reason="Live Gemini API tests disabled by default. Set OPTHIRE_RUN_LIVE_TESTS=1 to run.",
)
def test_live_gemini_single_prompt():
    from langchain_google_genai import ChatGoogleGenerativeAI
    from utils.config import GOOGLE_API_KEY

    assert GOOGLE_API_KEY and GOOGLE_API_KEY != "test_placeholder_key", (
        "Valid GOOGLE_API_KEY is required for live integration test."
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )
    response = llm.invoke("Reply with exactly the word: PONG")
    assert "PONG" in response.content.strip().upper()
