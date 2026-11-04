"""
Hiring report schemas for Agent 7 (Hiring Report Generator).
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class HiringReportRequest(BaseModel):
    """Input payload for Agent 7 (Hiring Report Generator)."""
    resume: Dict[str, Any] = Field(..., description="Parsed candidate resume JSON")
    job_description: Dict[str, Any] = Field(..., description="Parsed target job description JSON")
    match_result: Dict[str, Any] = Field(..., description="ATS match result JSON")
    skill_gap: Dict[str, Any] = Field(..., description="Skill gap report JSON")
    interview_summary: Dict[str, Any] = Field(..., description="AI interview summary JSON")


class CandidateDetails(BaseModel):
    name: Optional[str] = Field(default="", description="Candidate name")
    target_role: Optional[str] = Field(default="", description="Role applied for")
    candidate_summary: Optional[str] = Field(default="", description="Candidate profile summary")

    model_config = ConfigDict(extra="allow")


class ReportScores(BaseModel):
    resume_match_score: Union[int, float] = Field(..., description="Resume match score (0-100)")
    interview_score: Union[int, float] = Field(..., description="Interview performance score (0-100)")
    final_hiring_score: Union[int, float] = Field(..., description="Synthesized hiring score (0-100)")
    decision_confidence: Union[int, float] = Field(..., description="AI confidence in decision (0-100)")

    model_config = ConfigDict(extra="allow")


class ResumeEvaluationSection(BaseModel):
    matched_skills: List[str] = Field(default_factory=list, description="Verified matching skills")
    missing_skills: List[str] = Field(default_factory=list, description="Unverified or missing skills")
    key_strengths: List[str] = Field(default_factory=list, description="Highlighted strengths")
    key_weaknesses: List[str] = Field(default_factory=list, description="Highlighted weaknesses")
    summary: Optional[str] = Field(default="", description="Resume evaluation narrative")

    model_config = ConfigDict(extra="allow")


class InterviewEvaluationSection(BaseModel):
    performance_level: Optional[str] = Field(default="", description="Overall performance band")
    strongest_areas: List[str] = Field(default_factory=list, description="Best performing areas")
    weakest_areas: List[str] = Field(default_factory=list, description="Lowest performing areas")
    summary: Optional[str] = Field(default="", description="Interview evaluation narrative")

    model_config = ConfigDict(extra="allow")


class SkillGapEvaluationSection(BaseModel):
    priority_gaps: List[str] = Field(default_factory=list, description="Critical skill gaps")
    estimated_upskilling_time: Optional[str] = Field(default="", description="Estimated training time")
    development_summary: Optional[str] = Field(default="", description="Upskilling plan summary")

    model_config = ConfigDict(extra="allow")


class HiringRiskDetail(BaseModel):
    risk: str = Field(..., description="Identified risk")
    severity: str = Field(..., description="Severity level (Low, Medium, High)")
    reason: Optional[str] = Field(default="", description="Rationale for risk assessment")

    model_config = ConfigDict(extra="allow")


class FinalDecisionSection(BaseModel):
    recommendation: str = Field(..., description="Recommendation (Strong Hire, Hire, Consider, No Hire)")
    risk_level: str = Field(..., description="Risk level (Low, Medium, High)")
    reasoning: Optional[str] = Field(default="", description="Detailed rationale for the recommendation")
    next_action: Optional[str] = Field(default="", description="Suggested immediate next step")

    model_config = ConfigDict(extra="allow")


class HiringReportResponse(BaseModel):
    """Output contract for Agent 7 (Final Hiring Report)."""
    report_title: str = Field(default="OptHire AI Hiring Report")
    candidate: CandidateDetails
    executive_summary: str = Field(..., description="Executive overview")
    scores: ReportScores
    resume_evaluation: ResumeEvaluationSection
    interview_evaluation: InterviewEvaluationSection
    skill_gap_evaluation: SkillGapEvaluationSection
    hiring_risks: List[HiringRiskDetail] = Field(default_factory=list)
    key_reasons_to_hire: List[str] = Field(default_factory=list)
    key_reasons_for_caution: List[str] = Field(default_factory=list)
    final_decision: FinalDecisionSection
    recruiter_notes: Optional[str] = Field(default="")
    disclaimer: str = Field(
        default="This AI-generated report is decision support only. Final hiring decisions should include appropriate human review."
    )

    model_config = ConfigDict(extra="allow")
