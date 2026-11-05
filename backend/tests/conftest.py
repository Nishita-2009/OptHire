import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database.db import Base, get_db
from main import app


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


@pytest.fixture
def db_engine():
    """In-memory SQLite database engine isolated for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Scoped database session for database layer tests."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_client(db_session):
    """FastAPI TestClient with get_db overridden to use isolated test DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()



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
