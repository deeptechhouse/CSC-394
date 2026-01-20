"""
Test the actual question generation to see what the API returns.
"""
from question_generator import QuestionGenerator
from config import settings

print("=" * 60)
print("Question Generation Test")
print("=" * 60)
print(f"API Key configured: {'Yes' if settings.together_api_key else 'No'}")
print(f"Debug mode: {settings.debug}")
print()

try:
    generator = QuestionGenerator()
    print("[OK] QuestionGenerator initialized")
    
    print("\n" + "=" * 60)
    print("Generating a test question...")
    print("=" * 60)
    
    question = generator.generate_question(
        domain="Computer Science",
        professor_instructions="Create a test question",
        target_difficulty="Easy"
    )
    
    print("[OK] Question generated successfully!")
    print(f"\nQuestion ID: {question.question_id}")
    print(f"Question Text: {question.question_text[:200]}...")
    print(f"Difficulty: {question.difficulty}")
    print(f"Difficulty Score: {question.difficulty_score}")
    print(f"Has rubric: {question.rubric is not None}")
    print(f"Total points: {question.rubric.total_points if question.rubric else 0}")
    
except ValueError as e:
    print(f"\n[ERROR] ValueError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n[ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()
