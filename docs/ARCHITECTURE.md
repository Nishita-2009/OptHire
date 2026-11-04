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

## Orchestrator & Pipelines

- **`HiringPipeline` (`backend/orchestrator/hiring_pipeline.py`)**: Runs Agents 1 through 5 in automated sequence. Accepts PDF resume path and JD text, writes outputs to `outputs/`, and prepares the candidate for the interview stage.
- **Compatibility Layer (`backend/workflows/hiring_pipeline.py`)**: Re-exports `HiringPipeline` for cross-package and workflow backward compatibility.
