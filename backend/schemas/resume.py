"""
Resume schemas for parsing and structured extraction.
"""
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EducationItem(BaseModel):
    degree: Optional[str] = Field(default="", description="Degree or program title")
    college: Optional[str] = Field(default="", description="University or college name")
    year: Optional[str] = Field(default="", description="Graduation or enrollment year")
    cgpa: Optional[str] = Field(default="", description="CGPA or grade")

    model_config = ConfigDict(extra="allow")


class ExperienceItem(BaseModel):
    company: Optional[str] = Field(default="", description="Employer company name")
    role: Optional[str] = Field(default="", description="Job title / position")
    duration: Optional[str] = Field(default="", description="Employment duration")
    description: Optional[str] = Field(default="", description="Responsibilities and impact")

    model_config = ConfigDict(extra="allow")


class ProjectItem(BaseModel):
    title: Optional[str] = Field(default="", description="Project title")
    description: Optional[str] = Field(default="", description="Project description")
    technologies: List[str] = Field(default_factory=list, description="Technologies and frameworks used")

    model_config = ConfigDict(extra="allow")


class ResumeParsedResponse(BaseModel):
    """Output contract for Agent 1 (Resume Parser)."""
    name: Optional[str] = Field(default="", description="Candidate full name")
    email: Optional[str] = Field(default="", description="Email address")
    phone: Optional[str] = Field(default="", description="Phone number")
    location: Optional[str] = Field(default="", description="Candidate location")
    linkedin: Optional[str] = Field(default="", description="LinkedIn profile URL")
    github: Optional[str] = Field(default="", description="GitHub profile URL")
    portfolio: Optional[str] = Field(default="", description="Portfolio URL")
    summary: Optional[str] = Field(default="", description="Professional summary")
    education: List[EducationItem] = Field(default_factory=list, description="Educational history")
    experience: List[ExperienceItem] = Field(default_factory=list, description="Professional experience")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    projects: List[ProjectItem] = Field(default_factory=list, description="Key projects")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")
    languages: List[str] = Field(default_factory=list, description="Spoken/written languages")
    achievements: List[str] = Field(default_factory=list, description="Awards and achievements")

    model_config = ConfigDict(extra="allow")

