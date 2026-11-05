"""
Pipeline schemas for orchestrating Agents 1 through 5.
"""
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class PipelineResponse(BaseModel):
    """Output contract for full HiringPipeline execution."""
    status: str = Field(default="success", description="Pipeline execution status")
    resume: Dict[str, Any] = Field(..., description="Agent 1 parsed resume output")
    job_description: Dict[str, Any] = Field(..., description="Agent 2 parsed JD output")
    match_result: Dict[str, Any] = Field(..., description="Agent 3 resume match output")
    skill_gap: Dict[str, Any] = Field(..., description="Agent 4 skill gap output")
    interview: Dict[str, Any] = Field(..., description="Agent 5 interview generation output")

    model_config = ConfigDict(extra="allow")

