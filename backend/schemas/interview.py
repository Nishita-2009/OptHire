"""
Interview schemas for Agent 5 (Generator) and Agent 6 (Evaluator).
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class InterviewGenerateRequest(BaseModel):
    """Input payload for Agent 5 (Interview Generator)."""
    resume: Dict[str, Any] = Field(..., description="Parsed candidate resume JSON")
    job_description: Dict[str, Any] = Field(..., description="Parsed job description JSON")
    match_result: Dict[str, Any] = Field(..., description="ATS match evaluation JSON")
    skill_gap: Dict[str, Any] = Field(..., description="Skill gap report JSON")


class QuestionItem(BaseModel):
    question_id: str = Field(..., description="Unique question identifier (e.g. TECH_01)")
    question: str = Field(..., description="Interview question text")
    difficulty: str = Field(..., description="Difficulty level: Easy, Medium, or Hard")
    purpose: str = Field(..., description="Objective and assessment purpose")
    expected_answer_points: List[str] = Field(default_factory=list, description="Key points expected in strong answer")
    evaluation_criteria: List[str] = Field(default_factory=list, description="Rubric criteria for scoring")

    model_config = ConfigDict(extra="allow")


class QuestionDistribution(BaseModel):
    technical: int = Field(default=5)
    coding: int = Field(default=3)
    resume_based: int = Field(default=3)
    project_based: int = Field(default=3)
    missing_skill: int = Field(default=2)
    behavioral: int = Field(default=3)
    hr: int = Field(default=2)
    total: int = Field(default=21)

    model_config = ConfigDict(extra="allow")


class InterviewGenerationResponse(BaseModel):
    """Output contract for Agent 5 (21 Questions)."""
    candidate_level: Optional[str] = Field(default="", description="Evaluated candidate seniority")
    target_role: Optional[str] = Field(default="", description="Target job title")
    estimated_interview_duration: Optional[str] = Field(default="", description="Estimated time duration")
    overall_interview_difficulty: Optional[str] = Field(default="", description="Overall difficulty rating")
    interview_strategy: Optional[str] = Field(default="", description="Strategic rationale for interview design")
    question_distribution: QuestionDistribution = Field(default_factory=QuestionDistribution)
    technical_questions: List[QuestionItem] = Field(..., description="5 Technical questions")
    coding_questions: List[QuestionItem] = Field(..., description="3 Coding questions")
    resume_based_questions: List[QuestionItem] = Field(..., description="3 Resume-based questions")
    project_based_questions: List[QuestionItem] = Field(..., description="3 Project-based questions")
    missing_skill_questions: List[QuestionItem] = Field(..., description="2 Missing-skill awareness questions")
    behavioral_questions: List[QuestionItem] = Field(..., description="3 Behavioral questions")
    hr_questions: List[QuestionItem] = Field(..., description="2 HR questions")

    model_config = ConfigDict(extra="allow")


class AnswerEvaluationRequest(BaseModel):
    """Input payload for Agent 6 (Individual Answer Evaluator)."""
    question: Dict[str, Any] = Field(..., description="The interview question dictionary with rubric")
    candidate_answer: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="The candidate's spoken or written answer",
        examples=["In FastAPI, async def runs on the main event loop for non-blocking I/O..."],
    )


class AnswerEvaluationResponse(BaseModel):
    """Output contract for Agent 6 (Individual Answer Evaluation)."""
    score: Union[int, float] = Field(..., description="Numerical score (0-100)")
    rating: str = Field(..., description="Rating band: Excellent, Strong, Acceptable, Weak, or Poor")
    answer_summary: Optional[str] = Field(default="", description="Summary of candidate's response")
    strengths: List[str] = Field(default_factory=list, description="Demonstrated strengths")
    missing_points: List[str] = Field(default_factory=list, description="Omitted expected points")
    feedback: Optional[str] = Field(default="", description="Constructive feedback")
    ideal_answer: Optional[str] = Field(default="", description="Model reference answer")
    question_id: Optional[str] = Field(default="", description="Echoed question ID")
    question: Optional[str] = Field(default="", description="Echoed question text")
    candidate_answer: Optional[str] = Field(default="", description="Echoed candidate answer")
    category: Optional[str] = Field(default="", description="Question category")

    model_config = ConfigDict(extra="allow")


class InterviewSummaryResponse(BaseModel):
    """Output contract for Agent 6 (Final Interview Summary)."""
    overall_interview_score: Union[int, float] = Field(..., description="Overall interview score (0-100)")
    performance_level: str = Field(..., description="Performance band (e.g. Strong, Acceptable)")
    technical_performance: Optional[str] = Field(default="", description="Technical evaluation summary")
    problem_solving_performance: Optional[str] = Field(default="", description="Problem solving evaluation")
    communication_performance: Optional[str] = Field(default="", description="Communication evaluation")
    strongest_areas: List[str] = Field(default_factory=list, description="Candidate's best topics")
    weakest_areas: List[str] = Field(default_factory=list, description="Candidate's lowest scoring topics")
    key_strengths: List[str] = Field(default_factory=list, description="Top positive takeaways")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Coaching or gap recommendations")
    interview_summary: Optional[str] = Field(default="", description="Comprehensive interview narrative")
    recommendation: str = Field(..., description="Recommendation (Strong Hire, Hire, Consider, No Hire)")
    next_action: Optional[str] = Field(default="", description="Next recommended action")
    questions_generated: Optional[int] = Field(default=None, description="Total questions created")
    questions_answered: Optional[int] = Field(default=None, description="Total questions answered")

    model_config = ConfigDict(extra="allow")
