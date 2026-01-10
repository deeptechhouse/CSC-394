"""
Prompt templates for LLM interactions.
"""
from typing import Dict, Any, Optional


# Template for generating exam questions
QUESTION_GENERATION_TEMPLATE = """You are an expert educator creating an essay exam question in the domain of {domain}.

{professor_instructions}

Based on your knowledge of {domain} and any information provided above, please create a comprehensive essay exam question.

Your task is to:
1. Create an information sheet (background information) that may be displayed to the student as context for the exam question. This should be relevant domain information that helps frame the question.
2. Create an essay exam question based on the material and related to the displayed information. The question should test deep understanding, not just memorization.
3. Design a detailed grading rubric that specifies what information should be present in a satisfactory essay answer. Include specific criteria and point allocations.
4. Assess and rate the difficulty level of the question. Consider factors such as: complexity of concepts required, depth of analysis needed, synthesis of multiple ideas, and level of critical thinking expected.

Return your response as a valid Python dictionary with the following structure:
{{
    "background_info": "The background information to display to the student",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "context": "Additional context for understanding the question",
    "question_text": "The essay question to ask the student",
    "difficulty": "Easy",  # One of: "Easy", "Medium", "Hard"
    "difficulty_score": 5.5,  # Numerical score from 1.0 (easiest) to 10.0 (hardest)
    "rubric": {{
        "criteria": ["criterion1", "criterion2", "criterion3"],
        "points_per_criterion": {{"criterion1": 10.0, "criterion2": 15.0, "criterion3": 10.0}},
        "total_points": 35.0,
        "required_elements": ["element1", "element2"]
    }}
}}

Make sure the question is appropriate for the domain level and tests critical thinking and understanding, not just recall.

CRITICAL: You MUST return ONLY a valid Python dictionary. Do not include any explanatory text before or after the dictionary. Do not use markdown code blocks. Start your response directly with the opening brace { and end with the closing brace }. The dictionary must be valid Python syntax with proper quotes, commas, and brackets."""


# Template for grading student responses
GRADING_TEMPLATE = """You are an expert educator grading a student's essay response to an exam question.

DOMAIN: {domain}

QUESTION:
{question_text}

GRADING RUBRIC:
Criteria:
{criteria_list}

Points per criterion:
{points_per_criterion}

Total possible points: {total_points}

Required elements:
{required_elements}

BACKGROUND INFORMATION PROVIDED TO STUDENT:
{background_info}

KEY CONCEPTS STUDENT SHOULD KNOW:
{key_concepts}

ADDITIONAL CONTEXT:
{context}

STUDENT'S RESPONSE:
{student_response}

TIME SPENT: {time_spent_seconds} seconds

Your task is to:
1. Evaluate the student's response against each criterion in the rubric
2. Award points for each criterion based on how well the student addressed it
3. Check if required elements are present
4. Provide detailed explanations for why points were awarded or deducted
5. Identify strengths and weaknesses in the response
6. Provide constructive suggestions for improvement
7. Determine if the response is highly satisfactory (state P) or needs improvement

Return your response as a valid Python dictionary with the following structure:
{{
    "total_points_awarded": 28.5,
    "total_points_possible": 35.0,
    "percentage": 81.4,
    "state": "P",  # Use "P" if highly satisfactory (>=80%), otherwise use descriptive state
    "explanation": {{
        "overall_feedback": "Overall assessment of the response",
        "criterion_grades": [
            {{
                "criterion": "criterion1",
                "points_awarded": 9.0,
                "max_points": 10.0,
                "explanation": "Why these points were awarded",
                "satisfied": true
            }}
        ],
        "strengths": ["strength1", "strength2"],
        "weaknesses": ["weakness1", "weakness2"],
        "suggestions": ["suggestion1", "suggestion2"]
    }}
}}

Be thorough, fair, and constructive in your evaluation. Consider the depth of understanding demonstrated, not just keyword matching.

CRITICAL: You MUST return ONLY a valid Python dictionary. Do not include any explanatory text before or after the dictionary. Do not use markdown code blocks. Start your response directly with the opening brace { and end with the closing brace }. The dictionary must be valid Python syntax with proper quotes, commas, and brackets."""


def format_question_generation_prompt(
    domain: str,
    professor_instructions: str = "",
    target_difficulty: Optional[str] = None
) -> str:
    """
    Format the question generation prompt template.
    
    Args:
        domain: The subject domain for the question
        professor_instructions: Optional instructions from the professor
        target_difficulty: Optional target difficulty level ("Easy", "Medium", "Hard")
        
    Returns:
        Formatted prompt string
    """
    instructions = professor_instructions or "No specific instructions provided."
    
    if target_difficulty:
        difficulty_instruction = f"\n\nIMPORTANT: Generate a question with {target_difficulty} difficulty level. Adjust the complexity, depth of analysis required, and conceptual sophistication accordingly."
        instructions = instructions + difficulty_instruction
    
    return QUESTION_GENERATION_TEMPLATE.format(
        domain=domain,
        professor_instructions=instructions
    )


def format_grading_prompt(
    question: Dict[str, Any],
    student_response: str,
    time_spent_seconds: float
) -> str:
    """
    Format the grading prompt template.
    
    Args:
        question: Dictionary containing question data (from ExamQuestion model)
        student_response: The student's essay response
        time_spent_seconds: Time spent on the question
        
    Returns:
        Formatted prompt string
    """
    rubric = question.get("rubric", {})
    domain_info = question.get("domain_info", {})
    
    criteria_list = "\n".join([f"- {c}" for c in rubric.get("criteria", [])])
    points_str = "\n".join([f"- {k}: {v} points" for k, v in rubric.get("points_per_criterion", {}).items()])
    required_elements_str = "\n".join([f"- {e}" for e in rubric.get("required_elements", [])])
    key_concepts_str = "\n".join([f"- {c}" for c in domain_info.get("key_concepts", [])])
    
    return GRADING_TEMPLATE.format(
        domain=question.get("domain", "Unknown"),
        question_text=question.get("question_text", ""),
        criteria_list=criteria_list,
        points_per_criterion=points_str,
        total_points=rubric.get("total_points", 0),
        required_elements=required_elements_str,
        background_info=domain_info.get("background_info", ""),
        key_concepts=key_concepts_str,
        context=domain_info.get("context", ""),
        student_response=student_response,
        time_spent_seconds=time_spent_seconds
    )
