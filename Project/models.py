"""
Data models for the AI-powered exam system.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime


class GradingRubric(BaseModel):
    """Grading rubric for an exam question."""
    criteria: List[str]  # List of criteria that should be present in the answer
    points_per_criterion: Dict[str, float]  # Points allocated to each criterion
    total_points: float
    required_elements: List[str]  # Elements that must be present for full credit


class DomainInformation(BaseModel):
    """Domain-specific information for a question."""
    background_info: str  # Information displayed to student
    key_concepts: List[str]  # Concepts student should know
    context: str  # Additional context for the question


class ExamQuestion(BaseModel):
    """An exam question with its associated rubric and information."""
    question_id: str
    question_text: str
    rubric: GradingRubric
    domain_info: DomainInformation
    created_at: datetime
    domain: str  # Subject domain (e.g., "Computer Science", "History")
    difficulty: Optional[str] = None  # Difficulty rating: "Easy", "Medium", "Hard", or 1-10 scale
    difficulty_score: Optional[float] = None  # Numerical difficulty score (1-10)


class StudentResponse(BaseModel):
    """Student's response to an exam question."""
    question_id: str
    response_text: str
    time_spent_seconds: float
    submitted_at: datetime


class CriterionGrade(BaseModel):
    """Grade for a specific criterion."""
    criterion: str
    points_awarded: float
    max_points: float
    explanation: str
    satisfied: bool  # Whether the criterion was met


class GradeExplanation(BaseModel):
    """Detailed explanation of the grading."""
    overall_feedback: str
    criterion_grades: List[CriterionGrade]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class GradeResult(BaseModel):
    """Complete grading result for a student response."""
    question_id: str
    total_points_awarded: float
    total_points_possible: float
    percentage: float
    explanation: GradeExplanation
    graded_at: datetime
    state: str  # State P if highly satisfactory, otherwise other states


class ExamSession(BaseModel):
    """An exam session for a student."""
    session_id: str
    student_id: str
    questions: List[ExamQuestion]
    responses: List[StudentResponse]
    grades: List[GradeResult]
    started_at: datetime
    completed_at: Optional[datetime] = None
