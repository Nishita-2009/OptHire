import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Find .env in backend directory or workspace root
backend_dir = Path(__file__).resolve().parent.parent
backend_env = backend_dir / ".env"
root_env = backend_dir.parent / ".env"

if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
elif root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    # Allow test runners and CI environments to import agents without a live API key
    if (
        os.getenv("OPTHIRE_TEST_MODE", "").lower() in ("1", "true")
        or "pytest" in sys.modules
        or os.getenv("PYTEST_CURRENT_TEST")
    ):
        GOOGLE_API_KEY = "test_placeholder_key"
    else:
        # Default fallback or raise clear instructions
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not found in .env file. "
                "Please configure backend/.env using backend/.env.example."
            )
