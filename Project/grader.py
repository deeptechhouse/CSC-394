"""
Grading module for student responses.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from models import (
    ExamQuestion,
    StudentResponse,
    GradeResult,
    GradeExplanation,
    CriterionGrade
)
from prompts import format_grading_prompt
from llm_client import LLMClient


class Grader:
    """Grades student responses using LLM."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the grader.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
    
    def grade_response(
        self,
        question: ExamQuestion,
        student_response: StudentResponse
    ) -> GradeResult:
        """
        Grade a student's response to a question.
        
        Args:
            question: The exam question
            student_response: The student's response
            
        Returns:
            GradeResult object
        """
        # Convert question to dict for prompt formatting
        question_dict = {
            "domain": question.domain,
            "question_text": question.question_text,
            "rubric": {
                "criteria": question.rubric.criteria,
                "points_per_criterion": question.rubric.points_per_criterion,
                "total_points": question.rubric.total_points,
                "required_elements": question.rubric.required_elements
            },
            "domain_info": {
                "background_info": question.domain_info.background_info,
                "key_concepts": question.domain_info.key_concepts,
                "context": question.domain_info.context
            }
        }
        
        # Format the grading prompt
        prompt = format_grading_prompt(
            question_dict,
            student_response.response_text,
            student_response.time_spent_seconds
        )
        
        # Call LLM to grade
        try:
            llm_response = self.llm_client.grade_response(prompt)
        except ValueError as e:
            # If parsing failed, return a helpful error grade result
            return GradeResult(
                question_id=question.question_id,
                total_points_awarded=0.0,
                total_points_possible=question.rubric.total_points,
                percentage=0.0,
                explanation=GradeExplanation(
                    overall_feedback=f"Unable to parse AI grading response: {str(e)}. Please try submitting again or contact support if the issue persists.",
                    criterion_grades=[],
                    strengths=[],
                    weaknesses=["Unable to parse AI grading response - format error"],
                    suggestions=["Please try resubmitting your response", "If the problem persists, contact support"]
                ),
                graded_at=datetime.now(),
                state="Error"
            )
        
        # Ensure llm_response is a dictionary (should always be after our improvements)
        if not isinstance(llm_response, dict):
            raise ValueError(f"Expected dictionary from LLM, got {type(llm_response).__name__}: {str(llm_response)[:200]}")
        
        # Check if there's an error in the response (this shouldn't happen with new error handling)
        if "error" in llm_response:
            # If there was a parsing error, create a basic grade result
            return GradeResult(
                question_id=question.question_id,
                total_points_awarded=0.0,
                total_points_possible=question.rubric.total_points,
                percentage=0.0,
                explanation=GradeExplanation(
                    overall_feedback=llm_response.get("error", "Error processing response"),
                    criterion_grades=[],
                    strengths=[],
                    weaknesses=["Unable to parse AI grading response"],
                    suggestions=["Please try again or contact support"]
                ),
                graded_at=datetime.now(),
                state="Error"
            )
        
        # Extract grading data
        explanation_data = llm_response.get("explanation", {})
        
        # Ensure explanation_data is a dictionary
        if not isinstance(explanation_data, dict):
            explanation_data = {}
        
        # Build criterion grades
        criterion_grades = []
        llm_criterion_grades = explanation_data.get("criterion_grades", [])
        
        # If LLM provided criterion grades, use them
        if llm_criterion_grades and isinstance(llm_criterion_grades, list):
            for cg_data in llm_criterion_grades:
                # Ensure cg_data is a dictionary
                if not isinstance(cg_data, dict):
                    continue
                criterion_grade = CriterionGrade(
                    criterion=cg_data.get("criterion", ""),
                    points_awarded=cg_data.get("points_awarded", 0.0),
                    max_points=cg_data.get("max_points", 0.0),
                    explanation=cg_data.get("explanation", ""),
                    satisfied=cg_data.get("satisfied", False)
                )
                criterion_grades.append(criterion_grade)
        
        # If no criterion grades from LLM, create them from the rubric
        if not criterion_grades and question.rubric.criteria:
            # Distribute points proportionally if we have total_points_awarded
            total_awarded = llm_response.get("total_points_awarded", 0.0)
            points_per_criterion = question.rubric.points_per_criterion
            
            for criterion in question.rubric.criteria:
                max_pts = points_per_criterion.get(criterion, 0.0)
                # Estimate points awarded (proportional distribution)
                awarded_pts = 0.0
                if question.rubric.total_points > 0:
                    awarded_pts = (total_awarded / question.rubric.total_points) * max_pts
                
                criterion_grade = CriterionGrade(
                    criterion=criterion,
                    points_awarded=awarded_pts,
                    max_points=max_pts,
                    explanation="Grading details not available from AI response",
                    satisfied=awarded_pts >= (max_pts * 0.7)  # 70% threshold
                )
                criterion_grades.append(criterion_grade)
        
        # Build explanation
        explanation = GradeExplanation(
            overall_feedback=explanation_data.get("overall_feedback", ""),
            criterion_grades=criterion_grades,
            strengths=explanation_data.get("strengths", []),
            weaknesses=explanation_data.get("weaknesses", []),
            suggestions=explanation_data.get("suggestions", [])
        )
        
        # Get points from LLM response, but use question rubric as source of truth for total
        total_points_awarded = llm_response.get("total_points_awarded", 0.0)
        total_points_possible = question.rubric.total_points  # Use rubric from question, not LLM
        percentage = llm_response.get("percentage", 0.0)
        
        # Recalculate percentage if LLM didn't provide it or if it seems wrong
        if total_points_possible > 0:
            if percentage == 0.0 or abs(percentage - (total_points_awarded / total_points_possible * 100)) > 1.0:
                percentage = (total_points_awarded / total_points_possible) * 100
        
        # Build grade result
        grade_result = GradeResult(
            question_id=question.question_id,
            total_points_awarded=total_points_awarded,
            total_points_possible=total_points_possible,
            percentage=percentage,
            explanation=explanation,
            graded_at=datetime.now(),
            state=llm_response.get("state", "Needs Improvement")
        )
        
        return grade_result
