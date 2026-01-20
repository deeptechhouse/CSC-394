"""
FastAPI server for the AI-powered exam system.
"""
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from models import ExamQuestion, StudentResponse, GradeResult, ExamSession
from question_generator import QuestionGenerator
from grader import Grader
from config import settings

app = FastAPI(title="AI-Powered Exam System", version="1.0.0")

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage (in production, use a database)
sessions: Dict[str, ExamSession] = {}
question_generator = QuestionGenerator()
grader = Grader()


# Request models
class CreateExamRequest(BaseModel):
    domain: str
    num_questions: int = 3
    professor_instructions: Optional[str] = None
    student_id: str
    target_difficulty: Optional[str] = None  # "Easy", "Medium", "Hard", or None for mixed


class SubmitResponseRequest(BaseModel):
    question_id: str
    response_text: str
    time_spent_seconds: float


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/create-exam", response_class=HTMLResponse)
async def create_exam_page(request: Request):
    """Page for creating a new exam."""
    return templates.TemplateResponse("create_exam.html", {"request": request})


@app.post("/api/create-exam")
async def create_exam(request: CreateExamRequest):
    """Create a new exam session with generated questions."""
    try:
        # Check if API key is configured
        if not settings.together_api_key or settings.together_api_key.strip() == "":
            raise HTTPException(
                status_code=500,
                detail="API key not configured. Please set TOGETHER_API_KEY environment variable or create a .env file with your Together.ai API key."
            )
        
        # Generate questions
        questions = question_generator.generate_question_batch(
            domain=request.domain,
            count=request.num_questions,
            professor_instructions=request.professor_instructions or "",
            target_difficulty=request.target_difficulty
        )
        
        # Create session
        session_id = str(uuid.uuid4())
        session = ExamSession(
            session_id=session_id,
            student_id=request.student_id,
            questions=questions,
            responses=[],
            grades=[],
            started_at=datetime.now()
        )
        
        sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "num_questions": len(questions),
            "questions": [
                {
                    "question_id": q.question_id,
                    "question_text": q.question_text,
                    "difficulty": q.difficulty,
                    "difficulty_score": q.difficulty_score,
                    "domain_info": {
                        "background_info": q.domain_info.background_info,
                        "key_concepts": q.domain_info.key_concepts,
                        "context": q.domain_info.context
                    }
                }
                for q in questions
            ]
        }
    except ValueError as e:
        # More specific error message for validation errors
        error_msg = str(e)
        # Provide helpful guidance for common errors
        if "API key" in error_msg.lower():
            raise HTTPException(status_code=500, detail=error_msg)
        elif "closing brace" in error_msg.lower() or "' and end with" in error_msg:
            error_msg = "Failed to parse AI response. The AI may have returned an invalid format. Please check: 1) Your API key is valid, 2) The API is accessible, 3) Try again."
        raise HTTPException(status_code=500, detail=f"Failed to generate exam questions: {error_msg}")
    except Exception as e:
        # Log the full exception for debugging
        import traceback
        traceback.print_exc()
        error_detail = str(e)
        
        # Provide specific error messages for common issues
        if "API key" in error_detail.lower() or "authentication" in error_detail.lower():
            raise HTTPException(
                status_code=500,
                detail="API authentication failed. Please check your TOGETHER_API_KEY is correct and set in your .env file or environment variables."
            )
        elif "rate limit" in error_detail.lower():
            raise HTTPException(status_code=500, detail="API rate limit exceeded. Please wait a moment and try again.")
        elif "timeout" in error_detail.lower():
            raise HTTPException(status_code=500, detail="API request timed out. The service may be slow. Please try again.")
        elif "connection" in error_detail.lower():
            raise HTTPException(status_code=500, detail="Could not connect to the AI service. Please check your internet connection and try again.")
        elif "closing brace" in error_detail.lower() or "' and end with" in error_detail:
            error_detail = "Failed to parse AI response. The AI may have returned an invalid format. Please check: 1) Your API key is valid, 2) The API is accessible, 3) Try again."
        elif len(error_detail) > 300:
            # Truncate very long error messages but keep important parts
            error_detail = error_detail[:300] + "..."
        
        raise HTTPException(status_code=500, detail=f"Error creating exam: {error_detail}")


@app.get("/exam/{session_id}", response_class=HTMLResponse)
async def exam_page(request: Request, session_id: str):
    """Exam interface page."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    session = sessions[session_id]
    
    # Find current question (first unanswered)
    answered_question_ids = {r.question_id for r in session.responses}
    current_question = None
    current_index = 0
    
    for i, q in enumerate(session.questions):
        if q.question_id not in answered_question_ids:
            current_question = q
            current_index = i
            break
    
    if current_question is None:
        # All questions answered, show results
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "session": session,
                "all_complete": True
            }
        )
    
    return templates.TemplateResponse(
        "exam.html",
        {
            "request": request,
            "session": session,
            "question": current_question,
            "question_index": current_index + 1,
            "total_questions": len(session.questions)
        }
    )


@app.post("/api/submit-response")
async def submit_response(
    session_id: str = Form(...),
    question_id: str = Form(...),
    response_text: str = Form(...),
    time_spent_seconds: float = Form(...)
):
    """Submit a student response to a question."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    session = sessions[session_id]
    
    # Find the question
    question = None
    for q in session.questions:
        if q.question_id == question_id:
            question = q
            break
    
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Create student response
    student_response = StudentResponse(
        question_id=question_id,
        response_text=response_text,
        time_spent_seconds=time_spent_seconds,
        submitted_at=datetime.now()
    )
    
    session.responses.append(student_response)
    
    # Grade the response
    try:
        grade_result = grader.grade_response(question, student_response)
        session.grades.append(grade_result)
    except ValueError as e:
        # More specific error for parsing/validation issues
        error_msg = str(e)
        if "parse" in error_msg.lower() or "invalid format" in error_msg.lower():
            error_msg = "Failed to parse AI grading response. The AI may have returned an invalid format. Please try submitting your response again."
        raise HTTPException(status_code=500, detail=f"Error grading response: {error_msg}")
    except Exception as e:
        # General error handling
        error_detail = str(e)
        if len(error_detail) > 300:
            error_detail = error_detail[:300] + "..."
        raise HTTPException(status_code=500, detail=f"Error grading response: {error_detail}")
    
    # Check if exam is complete
    if len(session.responses) == len(session.questions):
        session.completed_at = datetime.now()
    
    return {
        "success": True,
        "grade": {
            "total_points_awarded": grade_result.total_points_awarded,
            "total_points_possible": grade_result.total_points_possible,
            "percentage": grade_result.percentage,
            "state": grade_result.state
        }
    }


@app.get("/results/{session_id}", response_class=HTMLResponse)
async def results_page(request: Request, session_id: str):
    """Results page showing all grades."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    session = sessions[session_id]
    
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "session": session,
            "all_complete": len(session.responses) == len(session.questions)
        }
    )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data as JSON."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session.session_id,
        "student_id": session.student_id,
        "num_questions": len(session.questions),
        "num_responses": len(session.responses),
        "num_grades": len(session.grades),
        "started_at": session.started_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
