"""
Skill gap schemas for Agent 4 (Skill Gap Analyzer).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SkillGapRequest(BaseModel):
    """Input payload for Agent 4 (Skill Gap Analyzer)."""
    resume: Dict[str, Any] = Field(..., description="Parsed candidate resume JSON")
    job_description: Dict[str, Any] = Field(..., description="Parsed target job description JSON")
    match_result: Dict[str, Any] = Field(..., description="ATS match result JSON from Agent 3")


class MissingSkillDetail(BaseModel):
    skill: str = Field(..., description="Missing skill name")
    priority: Optional[str] = Field(default="", description="Priority (High, Medium, Low)")
    reason: Optional[str] = Field(default="", description="Why this skill is needed for the role")
    estimated_learning_time: Optional[str] = Field(default="", description="Estimated time to acquire competency")
    expected_score_improvement: Optional[str] = Field(default="", description="Projected match score boost")

    model_config = ConfigDict(extra="allow")


class LearningResourceDetail(BaseModel):
    skill: str = Field(..., description="Target skill name")
    resource: str = Field(..., description="Recommended course, book, or lab")
    type: Optional[str] = Field(default="", description="Resource type (Course, Book, Documentation)")

    model_config = ConfigDict(extra="allow")


class SkillGapResponse(BaseModel):
    """Output contract for Agent 4 (Skill Gap Analyzer)."""
    overall_gap_summary: Optional[str] = Field(default="", description="Summary of candidate skill gaps")
    missing_skills: List[MissingSkillDetail] = Field(default_factory=list, description="Detailed missing skills")
    recommended_projects: List[str] = Field(default_factory=list, description="Recommended portfolio projects")
    recommended_certifications: List[str] = Field(default_factory=list, description="Recommended credentials")
    learning_resources: List[LearningResourceDetail] = Field(default_factory=list, description="Curated learning links")
    career_advice: Optional[str] = Field(default="", description="Strategic career advice")
    estimated_total_learning_time: Optional[str] = Field(default="", description="Total estimated upskilling time")

    model_config = ConfigDict(extra="allow")
