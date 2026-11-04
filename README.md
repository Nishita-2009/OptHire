# OptHire — AI-Powered Candidate Evaluation & Recruitment Platform

OptHire is an intelligent recruitment decision-support platform designed to streamline candidate evaluation, analyze skill gaps, generate tailored technical interviews, score candidate responses, and synthesize comprehensive, evidence-based hiring reports using Google Gemini.

> **Ethical Hiring Notice:** OptHire operates strictly as an intelligent decision-support system to empower recruiters and hiring managers. It does not make autonomous employment decisions; all recommendations require human review.

---

## 1. Core Capabilities & The 7 AI Agents

OptHire orchestrates seven specialized AI agents working sequentially or independently:

| Agent | Module | Description | Input | Output |
|---|---|---|---|---|
| **1. Resume Parser** | `agents.resume_parser` | Extracts structured candidate details from PDF resumes | PDF file upload | Structured JSON (skills, experience, education, projects) |
| **2. Job Description Parser** | `agents.jd_parser` | Parses job descriptions into requirements and qualifications | Raw JD text | Structured JSON (required/preferred skills, responsibilities) |
| **3. Resume Matcher** | `agents.resume_matcher` | Compares candidate credentials against role requirements | Resume & JD JSON | Match scores (0–100), strengths, weaknesses, recommendation |
| **4. Skill Gap Analyzer** | `agents.skill_gap` | Identifies missing skills and designs upskilling paths | Resume, JD & Match JSON | Prioritized missing skills, courses, project recommendations |
| **5. Interview Generator** | `agents.interview_generator` | Generates 21 personalized questions across 7 distinct categories | Resume, JD, Match & Gap JSON | 21 validated interview questions with rubrics & difficulty |
| **6. Interview Evaluator** | `agents.interview_evaluator` | Evaluates answers against rubrics and produces session summaries | Question rubric & Candidate answer | Scored answers, feedback, and final interview performance |
| **7. Hiring Report Generator** | `agents.hiring_report` | Synthesizes full candidate journey into executive hiring report | Outputs from Agents 1–6 | Executive summary, scores, risks, final recommendation |

---

## 2. System Architecture

```
                    +---------------------------+
                    | Candidate Resume (PDF)    |
                    +-------------+-------------+
                                  |
                                  v
+------------------------+   +------------------------+
| 1. Resume Parser Agent |   | 2. JD Parser Agent     |
+-----------+------------+   +-----------+------------+
            |                            |
            +-------------+--------------+
                          |
                          v
            +-----------------------------+
            | 3. Resume Matcher Agent     |
            +-------------+---------------+
                          |
                          v
            +-----------------------------+
            | 4. Skill Gap Analyzer Agent |
            +-------------+---------------+
                          |
                          v
            +-----------------------------+
            | 5. Interview Generator      |
            |    (21 Targeted Questions)  |
            +-------------+---------------+
                          |
                          v
            +-----------------------------+
            | 6. Interview Evaluator      |
            |    (Rubric-Based Scoring)   |
            +-------------+---------------+
                          |
                          v
            +-----------------------------+
            | 7. Hiring Report Generator  |
            |    (Executive Synthesis)    |
            +-----------------------------+
```

---

## 3. Technology Stack

- **Backend Framework**: FastAPI 0.138+ with Uvicorn
- **AI Model**: Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`
- **Language & Runtime**: Python 3.13+
- **Data Validation & Schemas**: Pydantic v2
- **Document Processing**: `pypdf`
- **Testing Framework**: `pytest` & `httpx` (`TestClient`)
- **Frontend (Future Phase)**: React 19 (scaffolded in `frontend/`)

---

## 4. Installation & Setup (Windows PowerShell)

### Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Google Gemini API Key

### 1. Clone & Environment Setup
```powershell
# Clone repository
git clone https://github.com/Nishita-2009/OptHire.git
cd OptHire

# Create virtual environment
python -m venv backend/venv

# Activate virtual environment in PowerShell
.\backend\venv\Scripts\Activate.ps1

# Install consolidated dependencies
pip install -r backend/requirements.txt
```

### 2. Configuration
Copy the example environment file and set your Gemini API key:
```powershell
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```ini
GOOGLE_API_KEY=your_actual_gemini_api_key_here
PORT=8000
HOST=127.0.0.1
DEBUG=false
```

---

## 5. Starting the FastAPI Server

### Running via Uvicorn (Recommended)
From the project workspace root:
```powershell
$env:PYTHONPATH = "backend"
uvicorn main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

Alternatively, from the `backend/` directory:
```powershell
cd backend
python main.py
```

### Interactive API Documentation (Swagger & ReDoc)
Once the server is running, open your browser:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 6. REST API Endpoints & Sample Payloads

### `GET /health`
Returns operational status without invoking Gemini.
- **Response**: `200 OK`
```json
{
  "status": "ok",
  "app": "OptHire API",
  "version": "1.0.0"
}
```

### `POST /api/v1/resumes/parse`
Parses candidate credentials from an uploaded PDF.
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (PDF file, max 10MB)
- **Response**: `200 OK` with `ResumeParsedResponse`

### `POST /api/v1/jobs/parse`
Parses job description text into structured requirements.
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "job_description": "We are seeking a Backend Engineer with 2+ years of experience in Python, FastAPI, and PostgreSQL. Responsibilities include building scalable REST APIs."
}
```

### `POST /api/v1/match`
Evaluates resume against job description.
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "resume": { "name": "Alex Morgan", "skills": ["Python", "FastAPI", "SQL"] },
  "job_description": { "job_title": "Backend Engineer", "required_skills": ["Python", "FastAPI", "SQL"] }
}
```

### `POST /api/v1/skill-gap`
Identifies missing skills and tailored learning plan.
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "resume": { "skills": ["Python", "FastAPI"] },
  "job_description": { "required_skills": ["Python", "FastAPI", "Kubernetes"] },
  "match_result": { "overall_match_score": 85, "missing_skills": ["Kubernetes"] }
}
```

### `POST /api/v1/interview/generate`
Generates 21 personalized interview questions across 7 categories.
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "resume": { "name": "Alex Morgan", "skills": ["Python", "FastAPI"] },
  "job_description": { "job_title": "Backend Engineer", "required_skills": ["Python", "FastAPI"] },
  "match_result": { "overall_match_score": 88 },
  "skill_gap": { "missing_skills": [{ "skill": "Kubernetes", "priority": "Medium" }] }
}
```

### `POST /api/v1/interview/evaluate`
Evaluates a single candidate answer against a question rubric.
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "question": {
    "question_id": "TECH_01",
    "question": "How do FastAPI async endpoints differ from sync endpoints?",
    "category": "Technical",
    "difficulty": "Medium",
    "purpose": "Assess asyncio understanding",
    "expected_answer_points": ["Event loop non-blocking I/O", "Threadpool delegation"],
    "evaluation_criteria": ["Clarity and correctness"]
  },
  "candidate_answer": "Async endpoints run directly on the event loop for non-blocking I/O, whereas sync endpoints are offloaded to an anyio worker threadpool."
}
```

### `POST /api/v1/reports/generate`
Synthesizes candidate journey into final hiring report.
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "resume": { "name": "Alex Morgan", "skills": ["Python", "FastAPI"] },
  "job_description": { "job_title": "Backend Engineer" },
  "match_result": { "overall_match_score": 88 },
  "skill_gap": { "overall_gap_summary": "Minor gap in orchestration" },
  "interview_summary": { "overall_interview_score": 90, "performance_level": "Strong", "recommendation": "Hire" }
}
```

### `POST /api/v1/pipeline/run`
Executes Agents 1 to 5 sequentially via `HiringPipeline`.
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `file`: PDF file
  - `job_description`: string

---

## 7. Running Tests

### Automated Mocked Test Suite (Zero Quota Consumed)
The automated suite runs 69 unit and route tests using mocked boundaries:
```powershell
# From workspace root
$env:PYTHONPATH = "backend"
pytest backend/tests -v
```

### Optional Live Gemini Integration Test
To run the live integration test that verifies actual Gemini Developer API connectivity:
```powershell
$env:PYTHONPATH = "backend"
$env:OPTHIRE_RUN_LIVE_TESTS = "1"
pytest backend/tests/test_integration_optional.py -v
```

---

## 8. Current Limitations & Next Steps

### Limitations in Current Phase (Phase 2)
1. **No Authentication**: The API currently has no user authentication or API key enforcement on endpoints; it is suitable for local development and private networks only.
2. **Ephemeral Persistence**: Agent results and pipelines currently operate in memory and temporary files; persistent database storage (PostgreSQL/SQLAlchemy) is deferred to Phase 3.
3. **Frontend Not Connected**: The React application in `frontend/` is not yet connected to the FastAPI backend endpoints.
