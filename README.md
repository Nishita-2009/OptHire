# OptHire — AI-Powered Candidate Evaluation & Recruitment Platform

OptHire is an intelligent recruitment decision-support platform designed to streamline candidate evaluation, analyze skill gaps, generate tailored technical interviews, score candidate responses, and synthesize comprehensive, evidence-based hiring reports using Google Gemini.

> **Ethical Hiring Notice:** OptHire operates strictly as an intelligent decision-support system to empower recruiters and hiring managers. It does not make autonomous employment decisions; all recommendations require human review.

---

## 1. Core Capabilities & The 7 AI Agents

OptHire orchestrates seven specialized AI agents working sequentially or independently:

| Agent | Module | Description | Input | Output |
|---|---|---|---|---|
| **1. Resume Parser** | `agents.resume_parser` | Extracts structured candidate details from PDF resumes or text | PDF file or text | Structured JSON (skills, experience, education, projects) |
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

- **AI Model**: Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`
- **Language & Runtime**: Python 3.13+
- **Document Processing**: `pypdf`
- **Data Validation & Schemas**: `pydantic`
- **Environment Management**: `python-dotenv`
- **Testing Framework**: `pytest`
- **Frontend (Future Phase)**: React 19 (scaffolded in `frontend/`)
- **API (Future Phase)**: FastAPI & Uvicorn (configured in dependencies)

---

## 4. Installation & Setup

### Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Google Gemini API Key

### Clone & Environment Setup
```bash
# 1. Clone repository
git clone https://github.com/Nishita-2009/OptHire.git
cd OptHire

# 2. Create and activate virtual environment
python -m venv backend/venv

# Windows PowerShell:
.\backend\venv\Scripts\Activate.ps1
# macOS / Linux:
source backend/venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt
```

### Configuration
Copy the example environment file and set your Gemini API key:
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```ini
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

---

## 5. Running Tests

### Automated Unit & Validation Suite (Zero Quota Consumed)
The automated test suite uses mocked Gemini responses to thoroughly test parsing, error handling, prompts, and schema contracts without incurring API costs:

```bash
# Windows PowerShell (from workspace root):
$env:PYTHONPATH = "backend"
pytest backend/tests -v

# macOS / Linux:
PYTHONPATH=backend pytest backend/tests -v
```

### Optional Live Gemini Integration Test
To verify live API connectivity against Gemini Developer API:
```bash
# Windows PowerShell:
$env:PYTHONPATH = "backend"
$env:OPTHIRE_RUN_LIVE_TESTS = "1"
pytest backend/tests/test_integration_optional.py -v
```

---

## 6. Running the Hiring Pipeline

To run the automated analysis pipeline (Agents 1 through 5) on a candidate resume and job description:

```bash
# Windows PowerShell:
$env:PYTHONPATH = "backend"
python backend/tests/test_hiring_pipeline.py
```

Outputs are automatically generated and saved in `outputs/`:
- `parsed_resume.json`
- `parsed_jd.json`
- `match_result.json`
- `skill_gap_report.json`
- `interview_questions.json`

### Running the Interactive AI Interview (Agent 6)
```bash
$env:PYTHONPATH = "backend"
python backend/tests/test_interview_evaluator.py
```

### Generating the Final Hiring Report (Agent 7)
```bash
$env:PYTHONPATH = "backend"
python backend/tests/test_hiring_report.py
```

---

## 7. Current Limitations & Next Steps

### Current Limitations
1. **Model Instantiation**: Agents initialize the LLM at module import time (`ChatGoogleGenerativeAI(model="gemini-2.5-flash")`). A factory pattern or centralized `GeminiService` should be implemented in Phase 2 to allow dynamic configuration and dependency injection.
2. **Terminal-Driven Execution**: Workflows currently run via Python scripts and orchestrators. Web API endpoints (FastAPI) and UI integrations are planned for subsequent phases.
3. **Data Persistence**: Outputs are currently persisted as individual JSON files in `outputs/` rather than a relational/document database.

### Recommended Next Phase
- **Phase 2: Service Layer & FastAPI Implementation**: Implement `GeminiService`, `FileService`, and `ReportService`, then expose REST endpoints for file uploads, pipeline execution, interactive interview sessions, and report retrieval.
