/**
 * OptHire Centralized API Client
 * Connects frontend UI to the FastAPI backend with structured error handling,
 * content-type awareness, and environment-configurable base URL.
 */

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL ||
  process.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Core HTTP dispatch helper
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const isFormData = options.body instanceof FormData;

  const defaultHeaders = {};
  if (!isFormData) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {}),
    },
  };

  try {
    const response = await fetch(url, config);
    let responseData = null;

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      responseData = await response.json();
    } else {
      const text = await response.text();
      try {
        responseData = JSON.parse(text);
      } catch {
        responseData = text;
      }
    }

    if (!response.ok) {
      // Extract human-readable error from FastAPI standard error response or string
      let errorMessage = `Request failed with status ${response.status}`;
      if (responseData && typeof responseData === "object") {
        if (responseData.detail) {
          if (typeof responseData.detail === "string") {
            errorMessage = responseData.detail;
          } else if (Array.isArray(responseData.detail)) {
            // Pydantic validation error array
            errorMessage = responseData.detail
              .map((err) => `${err.loc ? err.loc.join(".") + ": " : ""}${err.msg}`)
              .join("; ");
          } else {
            errorMessage = JSON.stringify(responseData.detail);
          }
        } else if (responseData.error) {
          errorMessage = responseData.error;
        }
      }
      throw new ApiError(errorMessage, response.status, responseData);
    }

    return responseData;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network failures, CORS issues, or connection refused
    throw new ApiError(
      `Unable to connect to OptHire API at ${API_BASE_URL}. Ensure the backend dev server is running. (${err.message})`,
      0,
      null
    );
  }
}

export const api = {
  // System Health
  getHealth: () => request("/health"),

  // Candidates
  getCandidates: (skip = 0, limit = 50) =>
    request(`/api/v1/candidates?skip=${skip}&limit=${limit}`),

  getCandidate: (id) =>
    request(`/api/v1/candidates/${encodeURIComponent(id)}`),

  createCandidate: (payload) =>
    request("/api/v1/candidates", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  uploadResume: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/api/v1/candidates/upload-resume", {
      method: "POST",
      body: formData,
    });
  },

  getCandidateAnalyses: (candidateId) =>
    request(`/api/v1/candidates/${encodeURIComponent(candidateId)}/analyses`),

  // Jobs
  getJobs: (skip = 0, limit = 50) =>
    request(`/api/v1/jobs?skip=${skip}&limit=${limit}`),

  getJob: (id) =>
    request(`/api/v1/jobs/${encodeURIComponent(id)}`),

  createJob: (payload) =>
    request("/api/v1/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  parseJobDescription: (text) =>
    request("/api/v1/jobs/parse", {
      method: "POST",
      body: JSON.stringify({ job_description: text }),
    }),

  // Candidate-Job Analysis Runs
  createAnalysis: (candidateId, jobId) =>
    request("/api/v1/analysis", {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId, job_id: jobId }),
    }),

  getAnalysis: (id) =>
    request(`/api/v1/analysis/${encodeURIComponent(id)}`),

  getAnalysisReport: (id) =>
    request(`/api/v1/analysis/${encodeURIComponent(id)}/report`),

  // Interview Sessions & Answer Evaluations
  createInterviewSession: (payload) =>
    request("/api/v1/interviews", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getInterviewSession: (id) =>
    request(`/api/v1/interviews/${encodeURIComponent(id)}`),

  submitInterviewAnswer: (sessionId, questionId, answerText) =>
    request(`/api/v1/interviews/${encodeURIComponent(sessionId)}/answers`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, answer: answerText }),
    }),

  finalizeInterview: (sessionId) =>
    request(`/api/v1/interviews/${encodeURIComponent(sessionId)}/finalize`, {
      method: "POST",
    }),

  // Executive Hiring Reports
  createReport: (analysisRunId, interviewSessionId = null) =>
    request("/api/v1/reports", {
      method: "POST",
      body: JSON.stringify({
        analysis_run_id: analysisRunId,
        interview_session_id: interviewSessionId,
      }),
    }),

  getReport: (id) =>
    request(`/api/v1/reports/${encodeURIComponent(id)}`),
};

export { ApiError, API_BASE_URL };
export default api;
