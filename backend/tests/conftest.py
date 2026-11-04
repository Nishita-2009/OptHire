import json
from pathlib import Path
import pytest


class MockAIMessage:
    """Mock Gemini response object returned by ChatGoogleGenerativeAI.invoke."""

    def __init__(self, content: str):
        self.content = content


class MockLLM:
    """Mock LLM instance that returns MockAIMessage without making API calls."""

    def __init__(self, content: str):
        self.content = content

    def invoke(self, prompt):
        return MockAIMessage(self.content)


@pytest.fixture(scope="session")
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def synthetic_resume(fixtures_dir):
    with open(fixtures_dir / "synthetic_resume.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_jd(fixtures_dir):
    with open(fixtures_dir / "synthetic_jd.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_match(fixtures_dir):
    with open(fixtures_dir / "synthetic_match_result.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_skill_gap(fixtures_dir):
    with open(fixtures_dir / "synthetic_skill_gap.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_interview(fixtures_dir):
    with open(fixtures_dir / "synthetic_interview_questions.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_evaluations(fixtures_dir):
    with open(fixtures_dir / "synthetic_interview_evaluations.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_summary(fixtures_dir):
    with open(fixtures_dir / "synthetic_interview_summary.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def synthetic_report(fixtures_dir):
    with open(fixtures_dir / "synthetic_hiring_report.json", "r", encoding="utf-8") as f:
        return json.load(f)
