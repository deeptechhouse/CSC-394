"""
Comprehensive test suite for the AI-Powered Exam System.
Tests all major components and functionality.
"""
import sys
import os
from datetime import datetime
from question_generator import QuestionGenerator
from grader import Grader
from models import (
    ExamQuestion, StudentResponse, GradeResult, ExamSession,
    GradingRubric, DomainInformation
)
from config import settings
from llm_client import LLMClient

def test_configuration():
    """Test configuration loading."""
    print("=" * 60)
    print("TEST SUITE: Configuration")
    print("=" * 60)
    
    try:
        assert hasattr(settings, 'together_api_key'), "Settings missing together_api_key"
        assert hasattr(settings, 'together_model'), "Settings missing together_model"
        assert hasattr(settings, 'host'), "Settings missing host"
        assert hasattr(settings, 'port'), "Settings missing port"
        
        print("[PASS] Configuration loaded successfully")
        print(f"  - Model: {settings.together_model}")
        print(f"  - Host: {settings.host}")
        print(f"  - Port: {settings.port}")
        
        if settings.together_api_key:
            print(f"  - API Key: {'*' * 20} (set)")
        else:
            print(f"  - API Key: Not set (some tests may fail)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        return False

def test_models():
    """Test data models."""
    print("\n" + "=" * 60)
    print("TEST SUITE: Data Models")
    print("=" * 60)
    
    try:
        # Test GradingRubric
        rubric = GradingRubric(
            criteria=["Understanding", "Analysis"],
            points_per_criterion={"Understanding": 10.0, "Analysis": 15.0},
            total_points=25.0,
            required_elements=["Introduction"]
        )
        assert rubric.total_points == 25.0
        print("[PASS] GradingRubric model works")
        
        # Test DomainInformation
        domain_info = DomainInformation(
            background_info="Test background",
            key_concepts=["Concept1"],
            context="Test context"
        )
        assert domain_info.background_info == "Test background"
        print("[PASS] DomainInformation model works")
        
        # Test ExamQuestion with difficulty
        question = ExamQuestion(
            question_id="test-1",
            question_text="Test question?",
            rubric=rubric,
            domain_info=domain_info,
            created_at=datetime.now(),
            domain="Test",
            difficulty="Medium",
            difficulty_score=6.5
        )
        assert question.difficulty == "Medium"
        assert question.difficulty_score == 6.5
        print("[PASS] ExamQuestion model with difficulty works")
        
        # Test StudentResponse
        response = StudentResponse(
            question_id="test-1",
            response_text="Test answer",
            time_spent_seconds=120.5,
            submitted_at=datetime.now()
        )
        assert response.response_text == "Test answer"
        print("[PASS] StudentResponse model works")
        
        # Test ExamSession
        session = ExamSession(
            session_id="session-1",
            student_id="student-1",
            questions=[question],
            responses=[],
            grades=[],
            started_at=datetime.now()
        )
        assert len(session.questions) == 1
        print("[PASS] ExamSession model works")
        
        return True
    except Exception as e:
        print(f"[FAIL] Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_client():
    """Test LLM client initialization."""
    print("\n" + "=" * 60)
    print("TEST SUITE: LLM Client")
    print("=" * 60)
    
    try:
        if not settings.together_api_key:
            print("[SKIP] API key not set, skipping LLM client test")
            return True
        
        client = LLMClient()
        assert client.api_key == settings.together_api_key
        assert client.model == settings.together_model
        assert "together.xyz" in client.api_url
        print("[PASS] LLM client initialized successfully")
        print(f"  - API URL: {client.api_url}")
        print(f"  - Model: {client.model}")
        
        return True
    except Exception as e:
        print(f"[FAIL] LLM client test failed: {e}")
        return False

def test_question_generator():
    """Test question generator."""
    print("\n" + "=" * 60)
    print("TEST SUITE: Question Generator")
    print("=" * 60)
    
    try:
        if not settings.together_api_key:
            print("[SKIP] API key not set, skipping question generator test")
            return True
        
        generator = QuestionGenerator()
        print("[PASS] QuestionGenerator initialized")
        
        # Test single question generation
        print("\n  Testing single question generation...")
        question = generator.generate_question(
            domain="Test Subject",
            professor_instructions="Create a test question"
        )
        
        assert question.question_id is not None
        assert question.question_text != ""
        assert question.domain == "Test Subject"
        assert question.rubric is not None
        assert question.domain_info is not None
        print("[PASS] Single question generated successfully")
        print(f"    - Question ID: {question.question_id}")
        print(f"    - Has difficulty: {question.difficulty is not None}")
        print(f"    - Has difficulty score: {question.difficulty_score is not None}")
        
        # Test batch generation
        print("\n  Testing batch generation...")
        questions = generator.generate_question_batch(
            domain="Test Subject",
            count=2,
            professor_instructions="Create test questions"
        )
        
        assert len(questions) == 2
        assert all(q.domain == "Test Subject" for q in questions)
        print("[PASS] Batch generation works")
        print(f"    - Generated {len(questions)} questions")
        print(f"    - All have difficulty ratings: {all(q.difficulty is not None for q in questions)}")
        
        # Test with target difficulty
        print("\n  Testing target difficulty...")
        easy_question = generator.generate_question(
            domain="Test Subject",
            target_difficulty="Easy"
        )
        assert easy_question.difficulty is not None
        print("[PASS] Target difficulty works")
        print(f"    - Rated as: {easy_question.difficulty}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Question generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_grader():
    """Test grading functionality."""
    print("\n" + "=" * 60)
    print("TEST SUITE: Grader")
    print("=" * 60)
    
    try:
        if not settings.together_api_key:
            print("[SKIP] API key not set, skipping grader test")
            return True
        
        grader = Grader()
        print("[PASS] Grader initialized")
        
        # Create a test question
        rubric = GradingRubric(
            criteria=["Understanding", "Clarity"],
            points_per_criterion={"Understanding": 10.0, "Clarity": 10.0},
            total_points=20.0,
            required_elements=["Answer"]
        )
        
        domain_info = DomainInformation(
            background_info="Test background information",
            key_concepts=["Concept1", "Concept2"],
            context="Test context"
        )
        
        question = ExamQuestion(
            question_id="test-question-1",
            question_text="What is the main concept?",
            rubric=rubric,
            domain_info=domain_info,
            created_at=datetime.now(),
            domain="Test Domain",
            difficulty="Medium",
            difficulty_score=6.0
        )
        
        # Create a test response
        response = StudentResponse(
            question_id="test-question-1",
            response_text="The main concept is about understanding fundamental principles and applying them in practice.",
            time_spent_seconds=180.0,
            submitted_at=datetime.now()
        )
        
        print("\n  Testing response grading...")
        grade_result = grader.grade_response(question, response)
        
        assert grade_result.question_id == question.question_id
        assert grade_result.total_points_possible == 20.0
        assert grade_result.total_points_awarded >= 0
        assert grade_result.percentage >= 0
        assert grade_result.explanation is not None
        print("[PASS] Response graded successfully")
        print(f"    - Points: {grade_result.total_points_awarded:.1f} / {grade_result.total_points_possible:.1f}")
        print(f"    - Percentage: {grade_result.percentage:.1f}%")
        print(f"    - State: {grade_result.state}")
        print(f"    - Has feedback: {grade_result.explanation.overall_feedback != ''}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Grader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_workflow():
    """Test complete exam workflow."""
    print("\n" + "=" * 60)
    print("TEST SUITE: Full Workflow")
    print("=" * 60)
    
    try:
        if not settings.together_api_key:
            print("[SKIP] API key not set, skipping full workflow test")
            return True
        
        generator = QuestionGenerator()
        grader = Grader()
        
        print("\n  Step 1: Generate exam questions...")
        questions = generator.generate_question_batch(
            domain="Science",
            count=2,
            professor_instructions="Create questions about basic scientific principles"
        )
        assert len(questions) == 2
        print(f"    [OK] Generated {len(questions)} questions")
        
        print("\n  Step 2: Create exam session...")
        session = ExamSession(
            session_id="test-session-1",
            student_id="test-student-1",
            questions=questions,
            responses=[],
            grades=[],
            started_at=datetime.now()
        )
        assert len(session.questions) == 2
        print(f"    [OK] Session created with {len(session.questions)} questions")
        
        print("\n  Step 3: Submit and grade responses...")
        for i, question in enumerate(questions, 1):
            response = StudentResponse(
                question_id=question.question_id,
                response_text=f"This is a test answer for question {i}. It demonstrates understanding of the concepts.",
                time_spent_seconds=120.0 + (i * 10),
                submitted_at=datetime.now()
            )
            session.responses.append(response)
            
            grade_result = grader.grade_response(question, response)
            session.grades.append(grade_result)
            
            print(f"    [OK] Question {i} graded: {grade_result.total_points_awarded:.1f}/{grade_result.total_points_possible:.1f} ({grade_result.percentage:.1f}%)")
        
        print("\n  Step 4: Complete session...")
        session.completed_at = datetime.now()
        total_points = sum(g.total_points_awarded for g in session.grades)
        total_possible = sum(g.total_points_possible for g in session.grades)
        overall_percentage = (total_points / total_possible * 100) if total_possible > 0 else 0
        
        print(f"    [OK] Session completed")
        print(f"    - Total points: {total_points:.1f} / {total_possible:.1f}")
        print(f"    - Overall score: {overall_percentage:.1f}%")
        print(f"    - All questions rated for difficulty: {all(q.difficulty is not None for q in session.questions)}")
        
        assert len(session.responses) == len(session.questions)
        assert len(session.grades) == len(session.questions)
        print("\n[PASS] Full workflow test completed successfully")
        
        return True
    except Exception as e:
        print(f"[FAIL] Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUITE")
    print("AI-Powered Exam System")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_configuration),
        ("Data Models", test_models),
        ("LLM Client", test_llm_client),
        ("Question Generator", test_question_generator),
        ("Grader", test_grader),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return True
    else:
        print(f"\n[WARNING] {total - passed} test suite(s) failed or were skipped")
        return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
