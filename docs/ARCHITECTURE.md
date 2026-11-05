# OptHire Architecture & Agent Contracts

## System Overview

OptHire is an AI-powered talent acquisition and evaluation platform powered by Google Gemini (Gemini 2.5 Flash). The platform orchestrates 7 specialized AI agents across candidate resume parsing, job requirement extraction, matching, skill gap analysis, personalized interview generation, answer evaluation, and final hiring report synthesis.

```
+-----------------------------------------------------------------------------------------+
|                                    OPTHIRE ARCHITECTURE                                 |
+-----------------------------------------------------------------------------------------+

  [Candidate Resume PDF]                 [Job Description Text]
           |                                       |
           v                                       v
 +-------------------+                   +-------------------+
 |  AGENT 1: Resume  |                   |    AGENT 2: JD    |
 |      Parser       |                   |      Parser       |
 +-------------------+                   +-------------------+
           \                                       /
            \                                     /
             v                                   v
        +---------------------------------------------+
        |         AGENT 3: Resume Matcher             |
        |  (Skill, Experience & Education Matching)   |
        +---------------------------------------------+
                               |
                               v
        +---------------------------------------------+
        |        AGENT 4: Skill Gap Analyzer          |
        | (Missing Skills & Upskilling Learning Plan) |
        +---------------------------------------------+
                               |
                               v
        +---------------------------------------------+
        |        AGENT 5: Interview Generator         |
        | (21 Structured Personalized Qs across 7 cat)|
        +---------------------------------------------+
                               |
                               v
        +---------------------------------------------+
        |        AGENT 6: Interview Evaluator         |
        |  (Rubric-Based Answer Scoring & Summary)    |
        +---------------------------------------------+
                               |
                               v
        +---------------------------------------------+
        |       AGENT 7: Hiring Report Generator      |
        | (Holistic Executive Decision Support Report)|
        +---------------------------------------------+
```

---

## The 7 Core AI Agents

### Agent 1: Resume Parser (`backend/agents/resume_parser`)
- **Input**: Raw candidate PDF or plain text.
- **Output Contract**: JSON with `name`, `email`, `phone`, `location`, `linkedin`, `summary`, `education`, `experience`, `skills`, `projects`, `certifications`, `languages`, `achievements`.

### Agent 2: Job Description Parser (`backend/agents/jd_parser`)
- **Input**: Raw job description text.
- **Output Contract**: JSON with `company`, `job_title`, `experience`, `education`, `required_skills`, `preferred_skills`, `responsibilities`, `certifications`, `location`, `employment_type`, `salary`.

### Agent 3: Resume Matcher (`backend/agents/resume_matcher`)
- **Input**: Resume JSON and Job Description JSON.
- **Output Contract**: JSON with `overall_match_score` (0-100), `confidence_score`, `candidate_summary`, `skill_match`, `experience_match`, `education_match`, `matched_skills`, `missing_skills`, `strengths`, `weaknesses`, `risk_level`, `recommendation`.

### Agent 4: Skill Gap Analyzer (`backend/agents/skill_gap`)
- **Input**: Resume JSON, Job Description JSON, ATS Match Result JSON.
- **Output Contract**: JSON with `overall_gap_summary`, `missing_skills` (priority, learning time, score impact), `recommended_projects`, `recommended_certifications`, `learning_resources`, `career_advice`, `estimated_total_learning_time`.

### Agent 5: Interview Generator (`backend/agents/interview_generator`)
- **Input**: Resume JSON, Job Description JSON, Match Result JSON, Skill Gap JSON.
- **Output Contract**: JSON with 21 questions distributed across:
  - Technical (5)
  - Coding (3)
  - Resume-Based (3)
  - Project-Based (3)
  - Missing-Skill Awareness (2)
  - Behavioral (3)
  - HR (2)
- **Validation**: Enforces exact category counts, unique `question_id`, and difficulty bounds ("Easy", "Medium", "Hard").

### Agent 6: Interview Evaluator (`backend/agents/interview_evaluator`)
- **Input**: Interview Question dictionary and Candidate Answer string.
- **Output Contract**:
  - `evaluate_answer`: `score` (0-100), `rating`, `answer_summary`, `strengths`, `missing_points`, `feedback`, `ideal_answer`.
  - `generate_final_interview_summary`: Aggregates all evaluations into `overall_interview_score`, `performance_level`, `strongest_areas`, `weakest_areas`, `recommendation`, `next_action`.

### Agent 7: Hiring Report Generator (`backend/agents/hiring_report`)
- **Input**: Outputs from Agents 1 through 6.
- **Output Contract**: Validated comprehensive hiring report with `report_title`, `candidate`, `executive_summary`, `scores` (`resume_match_score`, `interview_score`, `final_hiring_score`, `decision_confidence`), `resume_evaluation`, `interview_evaluation`, `skill_gap_evaluation`, `hiring_risks`, `key_reasons_to_hire`, `key_reasons_for_caution`, `final_decision` (`recommendation`, `risk_level`, `reasoning`, `next_action`), and mandatory ethical disclaimer.

---

## Phase 3 Database & Persistence Architecture

OptHire utilizes **SQLAlchemy 2.x** with declarative ORM models and **Alembic** migrations. The database architecture is designed with strict separation between engine configuration, entity models, repository data access, and business services.

### Entity Relationship Model

```mermaid
erDiagram
    CANDIDATES ||--o{ ANALYSIS_RUNS : "initiates"
    CANDIDATES ||--o{ INTERVIEW_SESSIONS : "participates in"
    JOBS ||--o{ ANALYSIS_RUNS : "evaluated for"
    JOBS ||--o{ INTERVIEW_SESSIONS : "targeted by"
    ANALYSIS_RUNS ||--o| HIRING_REPORTS : "synthesizes"
    ANALYSIS_RUNS ||--o{ INTERVIEW_SESSIONS : "links to"
    INTERVIEW_SESSIONS ||--o{ INTERVIEW_QUESTIONS : "contains (21)"
    INTERVIEW_SESSIONS ||--o{ HIRING_REPORTS : "informs"
    INTERVIEW_QUESTIONS ||--o| INTERVIEW_ANSWERS : "evaluated by"

    CANDIDATES {
        string id PK "UUID"
        string full_name
        string email
        string phone
        text resume_text
        json parsed_resume_data
        datetime created_at
        datetime updated_at
    }

    JOBS {
        string id PK "UUID"
        string title
        string company
        text description
        json parsed_job_data
        datetime created_at
        datetime updated_at
    }

    ANALYSIS_RUNS {
        string id PK "UUID"
        string candidate_id FK
        string job_id FK
        string status "pending, completed, failed"
        json resume_parse_result
        json job_parse_result
        json match_result
        json skill_gap_result
        text pipeline_error
        datetime created_at
        datetime completed_at
    }

    INTERVIEW_SESSIONS {
        string id PK "UUID"
        string candidate_id FK
        string job_id FK
        string analysis_run_id FK
        string status "pending, in_progress, completed"
        int current_question_index
        int total_questions
        datetime started_at
        datetime completed_at
        json final_summary
        datetime created_at
        datetime updated_at
    }

    INTERVIEW_QUESTIONS {
        string id PK "UUID"
        string interview_session_id FK
        string question_identifier
        text question_text
        string category
        string difficulty
        text purpose
        json expected_points
        json evaluation_criteria
        int sequence_number
    }

    INTERVIEW_ANSWERS {
        string id PK "UUID"
        string interview_question_id FK "UNIQUE"
        text answer_text
        json evaluation_result
        float score
        datetime submitted_at
        datetime evaluated_at
    }

    HIRING_REPORTS {
        string id PK "UUID"
        string analysis_run_id FK
        string interview_session_id FK
        json report_data
        string recommendation
        float overall_score
        datetime created_at
        datetime updated_at
    }
```

### Database Engines & SQLite-to-PostgreSQL Portability

- **Default Database**: SQLite (`sqlite:///./opthire.db`), configured with:
  - Safe automatic directory creation
  - Multi-thread support (`check_same_thread=False`)
  - Request-scoped dependency injection via FastAPI `get_db`
- **PostgreSQL Ready**: Transition to PostgreSQL by setting the environment variable:
  ```bash
  DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/opthire
  ```
  Zero application code modifications required; connection pooling parameters (`pool_size=10`, `max_overflow=20`) activate automatically.

### Alembic Migrations
- Migration files are located in `backend/alembic/versions/`.
- Configured with `render_as_batch=True` to support SQLite table schema alter operations seamlessly.
- Initial schema version: `8121985b88eb_initial_normalized_schema.py`.

---

## Stateful Interview Session Workflow

```mermaid
stateDiagram-v2
    [*] --> Pending: POST /api/v1/interviews
    Pending --> InProgress: Questions Generated (Agent 5)
    InProgress --> InProgress: POST /answers (Agent 6 scores answer)
    InProgress --> Completed: All 21 questions answered OR POST /complete
    Completed --> ReportGenerated: POST /api/v1/reports (Agent 7 synthesis)
    ReportGenerated --> [*]
```

1. **Session Creation**:
   - `POST /api/v1/interviews` accepts `candidate_id` and `job_id`.
   - Invokes Agent 5 (`generate_interview`) to generate 21 personalized questions across 7 categories.
   - Bulk inserts questions into `interview_questions` ordered by sequence.
2. **Answer Submission & Scoring**:
   - `POST /api/v1/interviews/{id}/answers` accepts `question_id` and `answer`.
   - Checks question belongs to session and has not already been answered (enforced by DB unique constraint).
   - Invokes Agent 6 (`evaluate_answer`) using the stored rubric and expected answer points.
   - Saves scored answer in `interview_answers` and advances `current_question_index`.
3. **Session Finalization**:
   - Automatically upon answering the last question, or via `POST /api/v1/interviews/{id}/complete`.
   - Aggregates all submitted answer evaluations and invokes Agent 6 (`generate_final_interview_summary`).
   - Marks session `status="completed"`, records `completed_at`, and stores `final_summary`.
4. **Persistent Hiring Report**:
   - `POST /api/v1/reports` synthesizes candidate profile, match result, skill gap analysis, and interview summary via Agent 7 (`generate_hiring_report`).
   - Persists final report in `hiring_reports` table linked to `analysis_run_id`.
