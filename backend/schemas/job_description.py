"""
Job description schemas for input validation and structured parsing output.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionRequest(BaseModel):
    """Input payload for Agent 2 (Job Description Parser)."""
    job_description: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Raw job description text",
        examples=["Looking for a Senior Backend Engineer with 3+ years of Python and FastAPI experience."],
    )


class JobDescriptionParsedResponse(BaseModel):
    """Output contract for Agent 2 (Job Description Parser)."""
    company: Optional[str] = Field(default="", description="Hiring company name")
    job_title: Optional[str] = Field(default="", description="Job title")
    experience: Optional[str] = Field(default="", description="Required experience level")
    education: Optional[str] = Field(default="", description="Required education level")
    required_skills: List[str] = Field(default_factory=list, description="Mandatory technical and domain skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred or bonus skills")
    responsibilities: List[str] = Field(default_factory=list, description="Primary duties and responsibilities")
    certifications: List[str] = Field(default_factory=list, description="Required or preferred certifications")
    location: Optional[str] = Field(default="", description="Job location")
    employment_type: Optional[str] = Field(default="", description="Employment type (Full Time, Contract, etc.)")
    salary: Optional[str] = Field(default="", description="Salary range if specified")

    model_config = ConfigDict(extra="allow")

