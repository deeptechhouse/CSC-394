"""
Question generation module.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from models import ExamQuestion, GradingRubric, DomainInformation
from prompts import format_question_generation_prompt
from llm_client import LLMClient


class QuestionGenerator:
    """Generates exam questions using LLM."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the question generator.
        
        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
    
    def generate_question(
        self,
        domain: str,
        professor_instructions: str = "",
        question_id: Optional[str] = None,
        target_difficulty: Optional[str] = None
    ) -> ExamQuestion:
        """
        Generate a new exam question.
        
        Args:
            domain: Subject domain for the question
            professor_instructions: Optional instructions from professor
            question_id: Optional question ID (generated if not provided)
            target_difficulty: Optional target difficulty ("Easy", "Medium", "Hard")
            
        Returns:
            ExamQuestion object
        """
        # Format the prompt
        prompt = format_question_generation_prompt(domain, professor_instructions, target_difficulty)
        
        # Call LLM to generate question
        llm_response = self.llm_client.generate_question(prompt)
        
        # Validate that llm_response is a dictionary
        if not isinstance(llm_response, dict):
            error_msg = f"LLM returned invalid response type: {type(llm_response).__name__}"
            if isinstance(llm_response, str):
                error_msg += f". Response preview: {llm_response[:200]}"
            raise ValueError(error_msg)
        
        # Check if there's an error in the response
        if "error" in llm_response:
            error_msg = llm_response.get("error", "Unknown error from LLM")
            raw_response = llm_response.get("raw_response", "")
            if raw_response:
                error_msg += f". Response preview: {raw_response[:200]}"
            raise ValueError(f"Failed to generate question: {error_msg}")
        
        # Extract components
        background_info = llm_response.get("background_info", "")
        key_concepts = llm_response.get("key_concepts", [])
        context = llm_response.get("context", "")
        question_text = llm_response.get("question_text", "")
        difficulty = llm_response.get("difficulty", None)
        difficulty_score = llm_response.get("difficulty_score", None)
        
        # Validate essential fields
        if not question_text:
            raise ValueError("LLM response missing required field: question_text")
        
        rubric_data = llm_response.get("rubric", {})
        if not isinstance(rubric_data, dict):
            rubric_data = {}
        
        # Build rubric with validation
        criteria = rubric_data.get("criteria", [])
        if isinstance(criteria, str):
            criteria = [c.strip() for c in criteria.split(",") if c.strip()]
        elif not isinstance(criteria, list):
            criteria = []
        
        points_per_criterion = rubric_data.get("points_per_criterion", {})
        if not isinstance(points_per_criterion, dict):
            points_per_criterion = {}
        else:
            # Normalize numeric values for rubric points
            normalized_points = {}
            for key, value in points_per_criterion.items():
                try:
                    normalized_points[key] = float(value)
                except (ValueError, TypeError):
                    normalized_points[key] = 0.0
            points_per_criterion = normalized_points
        
        total_points = rubric_data.get("total_points", 0.0)
        try:
            total_points = float(total_points)
        except (ValueError, TypeError):
            total_points = 0.0
        
        required_elements = rubric_data.get("required_elements", [])
        if isinstance(required_elements, str):
            required_elements = [e.strip() for e in required_elements.split(",") if e.strip()]
        elif not isinstance(required_elements, list):
            required_elements = []
        
        # Ensure key_concepts is a list
        if isinstance(key_concepts, str):
            key_concepts = [c.strip() for c in key_concepts.split(",") if c.strip()]
        elif not isinstance(key_concepts, list):
            key_concepts = []

        # Normalize difficulty score to a float if possible
        if difficulty_score is not None:
            try:
                if isinstance(difficulty_score, str):
                    cleaned = difficulty_score.replace("/10", "").replace("out of 10", "")
                    difficulty_score = float(cleaned.strip())
                else:
                    difficulty_score = float(difficulty_score)
            except (ValueError, TypeError):
                difficulty_score = None

        # Normalize difficulty label when possible
        if isinstance(difficulty, str):
            difficulty_clean = difficulty.strip().capitalize()
            if difficulty_clean in {"Easy", "Medium", "Hard"}:
                difficulty = difficulty_clean
            else:
                difficulty = None
        
        rubric = GradingRubric(
            criteria=criteria,
            points_per_criterion=points_per_criterion,
            total_points=total_points,
            required_elements=required_elements
        )
        
        # Build domain information
        domain_info = DomainInformation(
            background_info=background_info,
            key_concepts=key_concepts,
            context=context
        )
        
        # Build question
        question = ExamQuestion(
            question_id=question_id or str(uuid.uuid4()),
            question_text=question_text,
            rubric=rubric,
            domain_info=domain_info,
            created_at=datetime.now(),
            domain=domain,
            difficulty=difficulty,
            difficulty_score=difficulty_score
        )
        
        return question
    
    def generate_question_batch(
        self,
        domain: str,
        count: int,
        professor_instructions: str = "",
        target_difficulty: Optional[str] = None
    ) -> list[ExamQuestion]:
        """
        Generate multiple exam questions.
        
        Args:
            domain: Subject domain
            count: Number of questions to generate
            professor_instructions: Optional instructions from professor
            target_difficulty: Optional target difficulty ("Easy", "Medium", "Hard")
            
        Returns:
            List of ExamQuestion objects
        """
        questions = []
        for _ in range(count):
            question = self.generate_question(domain, professor_instructions, target_difficulty=target_difficulty)
            questions.append(question)
        return questions
