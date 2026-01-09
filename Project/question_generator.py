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
        
        # Extract components
        background_info = llm_response.get("background_info", "")
        key_concepts = llm_response.get("key_concepts", [])
        context = llm_response.get("context", "")
        question_text = llm_response.get("question_text", "")
        difficulty = llm_response.get("difficulty", None)
        difficulty_score = llm_response.get("difficulty_score", None)
        
        rubric_data = llm_response.get("rubric", {})
        
        # Build rubric
        rubric = GradingRubric(
            criteria=rubric_data.get("criteria", []),
            points_per_criterion=rubric_data.get("points_per_criterion", {}),
            total_points=rubric_data.get("total_points", 0.0),
            required_elements=rubric_data.get("required_elements", [])
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
