# OptHire — AI-Powered Candidate Evaluation & Recruitment Platform

OptHire is an intelligent recruitment decision-support platform designed to streamline candidate evaluation, analyze skill gaps, generate tailored technical interviews, score candidate responses, and synthesize comprehensive, evidence-based hiring reports using Google Gemini.

> **Ethical Hiring Notice:** OptHire operates strictly as an intelligent decision-support system to empower recruiters and hiring managers. It does not make autonomous employment decisions; all recommendations require human review.

---

## 1. Core Capabilities & The 7 AI Agents

OptHire orchestrates seven specialized AI agents working sequentially, independently, or within stateful database-persisted interview sessions:

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
- **Database ORM**: SQLAlchemy 2.x
- **Database Migrations**: Alembic 1.13+
- **Default Database**: SQLite (`sqlite:///./opthire.db`), fully PostgreSQL-ready
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
Copy the example environment file:
```powershell
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```ini
GOOGLE_API_KEY=your_actual_gemini_api_key_here
PORT=8000
HOST=127.0.0.1
DEBUG=false
DATABASE_URL=sqlite:///./opthire.db
```

### 3. Database Migrations (Alembic)
Apply the initial normalized database schema:
```powershell
cd backend
alembic upgrade head
cd ..
```

To create a new migration after model changes:
```powershell
cd backend
alembic revision --autogenerate -m "add new column or table"
alembic upgrade head
cd ..
```

#### Switching from SQLite to PostgreSQL
Change `DATABASE_URL` in your `.env` without modifying any Python code:
```ini
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/opthire
```
Run `alembic upgrade head` to provision all tables on PostgreSQL.

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

## 6. REST API Endpoints Overview

### Health & Stateless Agent Endpoints (Phase 2)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check without calling Gemini |
| `POST` | `/api/v1/resumes/parse` | Parse uploaded PDF resume via Agent 1 |
| `POST` | `/api/v1/jobs/parse` | Parse job description text via Agent 2 |
| `POST` | `/api/v1/match` | ATS match resume vs job description via Agent 3 |
| `POST` | `/api/v1/skill-gap` | Analyze skill gaps and learning plan via Agent 4 |
| `POST` | `/api/v1/interview/generate` | Generate 21 interview questions via Agent 5 |
| `POST` | `/api/v1/interview/evaluate` | Evaluate candidate answer via Agent 6 |
| `POST` | `/api/v1/reports/generate` | Synthesize stateless hiring report via Agent 7 |
| `POST` | `/api/v1/pipeline/run` | Run Agents 1–5 sequentially via `HiringPipeline` |

### Persistent Entity & Stateful Interview Endpoints (Phase 3)

#### Candidate Management
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/candidates` | Register candidate profile with parsed resume JSON |
| `GET` | `/api/v1/candidates/{id}` | Retrieve candidate profile and resume data by UUID |
| `GET` | `/api/v1/candidates` | List candidates with pagination (`skip`, `limit`) |
| `GET` | `/api/v1/candidates/{id}/analysis` | List all analysis runs for a candidate |

#### Job Openings
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/jobs` | Create a job posting with title, company, description |
| `GET` | `/api/v1/jobs/{id}` | Retrieve job details and structured requirements |
| `GET` | `/api/v1/jobs` | List job postings with pagination |

#### Analysis Runs
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/analysis` | Execute match (Agent 3) & skill gap (Agent 4) and persist run |
| `GET` | `/api/v1/analysis/{id}` | Retrieve analysis inputs and results |
| `GET` | `/api/v1/analysis/{id}/report` | Retrieve persisted hiring report for an analysis run |

#### Stateful Interview Sessions
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/interviews` | Create session; automatically generates 21 questions via Agent 5 |
| `GET` | `/api/v1/interviews/{id}` | Get session status, current active question, and progress |
| `GET` | `/api/v1/interviews/{id}/questions` | List all 21 ordered questions and answer status |
| `POST` | `/api/v1/interviews/{id}/answers` | Submit answer; scores with Agent 6; auto-completes on final question |
| `GET` | `/api/v1/interviews/{id}/answers` | List submitted answers and evaluations |
| `POST` | `/api/v1/interviews/{id}/complete` | Explicitly complete interview and generate final summary via Agent 6 |

#### Persistent Hiring Reports
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/reports` | Synthesize and persist final hiring report via Agent 7 |
| `GET` | `/api/v1/reports/{id}` | Retrieve persisted hiring report by report UUID |

---

## 7. Running Tests

### Automated Test Suite (Zero Quota Consumed)
The automated test suite contains **89 unit, integration, database, and route tests**:
```powershell
# From workspace root
$env:PYTHONPATH = "backend"
pytest backend/tests -v
```

### Test Suite Structure
- `backend/tests/test_database.py`: 8 database tests (engine, models, CRUD, cascades, constraints, rollbacks)
- `backend/tests/test_interview_workflow.py`: 7 workflow service tests (session transitions, Agent 5 generation, Agent 6 answer scoring, auto-completion, report persistence)
- `backend/tests/test_persistent_routes.py`: 5 endpoint integration tests (candidates, jobs, analysis, interviews, reports)
- `backend/tests/test_agent_*.py`: 43 agent tests (import, prompts, schema validation across all 7 agents)
- `backend/tests/test_api_routes.py`: 19 API route tests (stateless Phase 2 endpoints)
- `backend/tests/test_pipeline.py`: Mocked orchestration pipeline test
- `backend/tests/test_services.py`: Utility & service layer tests
- `backend/tests/test_integration_optional.py`: Live Gemini API test (skipped by default)

### Optional Live Gemini Integration Test
```powershell
$env:PYTHONPATH = "backend"
$env:OPTHIRE_RUN_LIVE_TESTS = "1"
pytest backend/tests/test_integration_optional.py -v
```

---

## 8. Current Limitations & Next Steps

### Current Status (Phase 3 Completed)
1. **Persistent Database Layer**: Complete with normalized models, Alembic migrations, SQLite default, and PostgreSQL support.
2. **Stateful Interview Sessions**: Complete with automatic 21-question generation (Agent 5), rubric answer scoring (Agent 6), progress index tracking, duplicate prevention, and interview summary generation.
3. **Persisted Reports**: Complete with Agent 7 executive report synthesis and database linkage.
4. **Automated Test Coverage**: 89 passing tests with 100% mocked isolation.

### Scope for Future Phases
1. **Authentication & Authorization**: JWT token authentication, role-based access control (Recruiter, Hiring Manager, Candidate) deferred to Phase 4.
2. **Frontend UI Integration**: Connect React frontend in `frontend/` to the REST API endpoints.
3. **Real-time Updates**: WebSockets or SSE for interactive interview question streaming.
