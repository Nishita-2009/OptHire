"""
Match result schemas for Agent 3 (Resume Matcher).
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class MatchRequest(BaseModel):
    """Input payload for Agent 3 (Resume Matcher)."""
    resume: Dict[str, Any] = Field(..., description="Parsed resume JSON structure")
    job_description: Dict[str, Any] = Field(..., description="Parsed job description JSON structure")


class ScoreReason(BaseModel):
    score: Union[int, float] = Field(..., description="Category score (0-100)")
    reason: Optional[str] = Field(default="", description="Explanation of score assignment")

    model_config = ConfigDict(extra="allow")


class MatchResultResponse(BaseModel):
    """Output contract for Agent 3 (Resume Matcher)."""
    overall_match_score: Union[int, float] = Field(..., description="Overall match score (0-100)")
    confidence_score: Union[int, float] = Field(..., description="Confidence score (0-100)")
    candidate_summary: Optional[str] = Field(default="", description="Executive candidate fit summary")
    skill_match: ScoreReason = Field(..., description="Technical and domain skill evaluation")
    experience_match: ScoreReason = Field(..., description="Work experience duration and depth evaluation")
    education_match: ScoreReason = Field(..., description="Educational alignment evaluation")
    matched_skills: List[str] = Field(default_factory=list, description="Skills present in both resume and JD")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills missing from resume")
    strengths: List[str] = Field(default_factory=list, description="Candidate key strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified shortcomings or risks")
    risk_level: Optional[str] = Field(default="", description="Risk level (Low, Medium, High)")
    salary_fit: Optional[str] = Field(default="", description="Salary expectation fit")
    interview_difficulty: Optional[str] = Field(default="", description="Estimated interview difficulty")
    recommendation: Optional[str] = Field(default="", description="ATS recommendation")
    next_action: Optional[str] = Field(default="", description="Suggested recruiter next step")

    model_config = ConfigDict(extra="allow")
