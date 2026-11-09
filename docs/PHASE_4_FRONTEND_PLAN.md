# OptHire — Phase 4: Frontend Architecture & Implementation Plan

## 1. Existing Frontend Architecture Audit

### 1.1 Discovery & Environment
- **Framework**: React 19.2.7 (`react`, `react-dom`).
- **Tooling / Build System**: Create React App 5.0.1 (`react-scripts`).
- **Initial State**: Vanilla CRA starter template (`App.js`, `App.css`, `index.js`, `index.css`, `App.test.js`).
- **Configured Dependencies**:
  - `react`: `^19.2.7`
  - `react-dom`: `^19.2.7`
  - `react-scripts`: `5.0.1`
  - `react-router-dom`: `^7.1.5` (client-side routing)
  - `lucide-react`: `^1.70.0` (accessible, lightweight UI iconography)
  - `@testing-library/react`: `^16.3.2`
  - `@testing-library/jest-dom`: `^6.9.1`

### 1.2 Environment Variable Convention
- Create React App recognizes environment variables prefixed with `REACT_APP_`.
- To support both CRA and Vite conventions smoothly, the centralized API client accepts:
  - `process.env.REACT_APP_API_BASE_URL`
  - `process.env.VITE_API_BASE_URL`
  - Default fallback: `http://127.0.0.1:8000`

---

## 2. Design System & Theme Foundations

### 2.1 Aesthetic Direction
- **Identity**: OptHire — Autonomous AI Recruitment & Evaluation SaaS.
- **Palette**:
  - Primary / Brand Navy: `#0A192F` (Deep Navy), `#1E3A8A` (Slate Navy)
  - Accent / Tech Blue: `#2563EB` (Electric Royal), `#3B82F6` (Sky Bright)
  - Success / Match Emerald: `#059669` / `#10B981`
  - Warning / Caution Amber: `#D97706` / `#F59E0B`
  - Danger / Gap Rose: `#DC2626` / `#EF4444`
  - Background Neutral: `#F8FAFC` (Canvas Gray), `#FFFFFF` (Card Surface)
  - Border & Dividers: `#E2E8F0` / `#CBD5E1`
  - Typography: System font stack prioritizing Inter / -apple-system / Segoe UI.

### 2.2 Reusable UI Component Primitives
- `Button`: Primary, secondary, outline, ghost, danger, with integrated loading spinners.
- `Card`: Structured container with header, body, footer, and elevated shadow variants.
- `Badge`: Status and score pill badges (e.g. "Provisional", "Completed", "Strong Hire", "Low Risk").
- `ScoreCard` / `MetricCard`: Circular or progress-bar metric cards displaying ATS match, interview, and hiring scores.
- `Alert` / `Notification`: Inline dismissible alerts and toast notifications for success/error feedback.
- `Modal` / `Dialog`: Accessible backdrop modal for registration, job creation, and confirmation.
- `EmptyState`: Contextual illustration and call-to-action when lists or tables are empty.
- `LoadingSkeleton` / `Spinner`: Clean skeleton placeholders avoiding layout shifts.

---

## 3. Application Shell & Routing Structure

### 3.1 Routing Matrix (`react-router-dom`)
- `/` or `/dashboard`: Executive dashboard with platform stats, recent candidate pipeline, recent jobs, and active analyses.
- `/candidates`: Candidate directory, resume upload modal, candidate detail view with parsed skills, experience, and historical analyses.
- `/jobs`: Job openings directory, JD text parsing/creation modal, job detail view with required and preferred skill tags.
- `/analysis`: Candidate-versus-Job ATS matching and skill gap workspace, triggering Agent 3 and Agent 4, with side-by-side match breakdown.
- `/interviews`: Persistent interview sessions hub, showing session status, question rubric, and provisional answer evaluation progress.
- `/reports`: Executive hiring reports hub, displaying provisional vs completed reports with breakdown metrics and recruiter notes.
- `/settings`: Environment and backend connection health monitor.

### 3.2 Shell Layout
```text
+--------------------------------------------------------------------------+
|  OPTHIRE (Logo)  | Search / Quick Actions | Backend Status: [● Healthy]  |  TopNav
+------------------+-------------------------------------------------------+
|  [Dashboard]     |                                                       |
|  [Candidates]    |                                                       |
|  [Jobs]          |               Main Application Outlet                 |
|  [Analysis]      |               (Responsive Grid / Cards)               |
|  [Interviews]    |                                                       |
|  [Reports]       |                                                       |
|  [Settings]      |                                                       |  SideNav
+------------------+-------------------------------------------------------+
```

---

## 4. Centralized API Client Architecture

### 4.1 Service Layer (`src/services/api.js`)
- Base URL configured from environment: `REACT_APP_API_BASE_URL || "http://127.0.0.1:8000"`.
- Unified `request(endpoint, options)` wrapper:
  - Automatically handles JSON payload serialization and header configuration.
  - Automatically handles `multipart/form-data` for resume file uploads.
  - Intercepts non-2xx HTTP responses, extracting backend `detail` messages into typed user-facing errors.
  - Configures timeouts and connection failure detection.

### 4.2 Endpoint Mapping
- **System**:
  - `GET /health` -> `api.getHealth()`
- **Candidates**:
  - `GET /api/v1/candidates` -> `api.getCandidates(skip, limit)`
  - `GET /api/v1/candidates/:id` -> `api.getCandidate(id)`
  - `POST /api/v1/candidates` -> `api.createCandidate(payload)`
  - `POST /api/v1/candidates/upload-resume` -> `api.uploadResume(file)` (Agent 1)
  - `GET /api/v1/candidates/:id/analyses` -> `api.getCandidateAnalyses(id)`
- **Jobs**:
  - `GET /api/v1/jobs` -> `api.getJobs(skip, limit)`
  - `GET /api/v1/jobs/:id` -> `api.getJob(id)`
  - `POST /api/v1/jobs` -> `api.createJob(payload)`
  - `POST /api/v1/jobs/parse` -> `api.parseJobDescription(text)` (Agent 2)
- **Analysis**:
  - `POST /api/v1/analysis` -> `api.createAnalysis(candidateId, jobId)` (Agent 3 & Agent 4)
  - `GET /api/v1/analysis/:id` -> `api.getAnalysis(id)`
  - `GET /api/v1/analysis/:id/report` -> `api.getAnalysisReport(id)`
- **Interviews**:
  - `POST /api/v1/interviews` -> `api.createInterviewSession(payload)` (Agent 5)
  - `GET /api/v1/interviews/:id` -> `api.getInterviewSession(id)`
  - `POST /api/v1/interviews/:id/answers` -> `api.submitInterviewAnswer(id, payload)` (Agent 6)
  - `POST /api/v1/interviews/:id/finalize` -> `api.finalizeInterview(id)` (Agent 6 Summary)
- **Reports**:
  - `POST /api/v1/reports` -> `api.createReport(analysisRunId, interviewSessionId)` (Agent 7)
  - `GET /api/v1/reports/:id` -> `api.getReport(id)`

---

## 5. Phase 4 Implementation Sequence

1. **Step 1 (Audit & Plan)**: Establish `docs/PHASE_4_FRONTEND_PLAN.md` and dependencies. *(Complete)*
2. **Step 2 (Design System & Styles)**:
   - Configure global CSS design tokens, typography, colors, animations, and CSS reset in `src/index.css`.
   - Implement reusable UI components (`src/components/ui/`).
3. **Step 3 (Application Shell)**:
   - Implement `Sidebar`, `TopNav`, `Layout`, `NotificationProvider`, and router setup in `src/App.js`.
4. **Step 4 (API Client)**:
   - Implement `src/services/api.js` with comprehensive error interception and mock-ready integration.
5. **Step 5 (First Real Workflow & Pages)**:
   - Implement `DashboardPage` (platform overview, live stats, quick actions).
   - Implement `CandidatesPage` & `CandidateDetailPage` (registration modal, PDF parsing, skill tags).
   - Implement `JobsPage` & `JobDetailPage` (job creation modal, JD auto-parser).
   - Implement `AnalysisPage` (interactive candidate-versus-job runner, match score gauges, skill gaps).
   - Implement `InterviewsPage` & `ReportsPage` (views for sessions and provisional/final hiring reports).
   - Implement `SettingsPage` (backend health ping, environment status).
6. **Step 6 (Verification & Build)**:
   - Execute frontend production build.
   - Run frontend unit/component tests.
   - Re-run backend regression tests.
