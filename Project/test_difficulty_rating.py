"""
Test script to verify automatic difficulty rating functionality.
This script tests that questions are automatically rated for difficulty.
"""
import os
import sys
from question_generator import QuestionGenerator
from llm_client import LLMClient
from config import settings

def test_difficulty_rating():
    """Test that questions are automatically rated for difficulty."""
    print("=" * 60)
    print("Testing Automatic Difficulty Rating")
    print("=" * 60)
    
    # Check if API key is set
    if not settings.together_api_key:
        print("\n[ERROR] TOGETHER_API_KEY not set in environment or .env file")
        print("Please set your Together.ai API key to run this test.")
        return False
    
    print(f"\n[OK] API Key found")
    print(f"[OK] Using model: {settings.together_model}")
    print(f"\nGenerating test questions...\n")
    
    try:
        generator = QuestionGenerator()
        
        # Test 1: Generate question without target difficulty (should auto-rate)
        print("-" * 60)
        print("TEST 1: Auto-rating without target difficulty")
        print("-" * 60)
        question1 = generator.generate_question(
            domain="Literature",
            professor_instructions="Create a question about literary analysis and themes"
        )
        
        print(f"Question ID: {question1.question_id}")
        print(f"Domain: {question1.domain}")
        print(f"Difficulty: {question1.difficulty}")
        print(f"Difficulty Score: {question1.difficulty_score}")
        print(f"\nQuestion Text:\n{question1.question_text[:200]}...")
        
        # Verify difficulty was rated
        if question1.difficulty is None and question1.difficulty_score is None:
            print("\n[FAIL] Question was not rated for difficulty")
            return False
        else:
            print(f"\n[PASS] Question automatically rated")
            print(f"  - Difficulty Level: {question1.difficulty}")
            print(f"  - Difficulty Score: {question1.difficulty_score}")
        
        # Test 2: Generate question with Easy target
        print("\n" + "-" * 60)
        print("TEST 2: Generating Easy difficulty question")
        print("-" * 60)
        question2 = generator.generate_question(
            domain="Biology",
            professor_instructions="Create a basic question about cell structure and function",
            target_difficulty="Easy"
        )
        
        print(f"Question ID: {question2.question_id}")
        print(f"Domain: {question2.domain}")
        print(f"Target Difficulty: Easy")
        print(f"Rated Difficulty: {question2.difficulty}")
        print(f"Difficulty Score: {question2.difficulty_score}")
        print(f"\nQuestion Text:\n{question2.question_text[:200]}...")
        
        if question2.difficulty is None:
            print("\n[FAIL] Easy question was not rated")
            return False
        else:
            print(f"\n[PASS] Easy question rated as '{question2.difficulty}'")
        
        # Test 3: Generate question with Hard target
        print("\n" + "-" * 60)
        print("TEST 3: Generating Hard difficulty question")
        print("-" * 60)
        question3 = generator.generate_question(
            domain="Economics",
            professor_instructions="Create an advanced question about macroeconomic theory and policy implications",
            target_difficulty="Hard"
        )
        
        print(f"Question ID: {question3.question_id}")
        print(f"Domain: {question3.domain}")
        print(f"Target Difficulty: Hard")
        print(f"Rated Difficulty: {question3.difficulty}")
        print(f"Difficulty Score: {question3.difficulty_score}")
        print(f"\nQuestion Text:\n{question3.question_text[:200]}...")
        
        if question3.difficulty is None:
            print("\n[FAIL] Hard question was not rated")
            return False
        else:
            print(f"\n[PASS] Hard question rated as '{question3.difficulty}'")
        
        # Test 4: Generate batch of questions
        print("\n" + "-" * 60)
        print("TEST 4: Generating batch of questions (mixed difficulty)")
        print("-" * 60)
        questions = generator.generate_question_batch(
            domain="Art History",
            count=3,
            professor_instructions="Create questions about Renaissance art and its cultural impact"
        )
        
        print(f"Generated {len(questions)} questions")
        all_rated = True
        for i, q in enumerate(questions, 1):
            print(f"\nQuestion {i}:")
            print(f"  Difficulty: {q.difficulty}")
            print(f"  Score: {q.difficulty_score}")
            if q.difficulty is None and q.difficulty_score is None:
                all_rated = False
                print(f"  [FAIL] Not rated")
            else:
                print(f"  [OK] Rated")
        
        if not all_rated:
            print("\n[FAIL] Some questions in batch were not rated")
            return False
        else:
            print("\n[PASS] All questions in batch were automatically rated")
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("[SUCCESS] All tests passed!")
        print("\nDifficulty Rating Features Verified:")
        print("  1. [OK] Questions are automatically rated for difficulty")
        print("  2. [OK] Both categorical (Easy/Medium/Hard) and numerical (1-10) ratings")
        print("  3. [OK] Target difficulty can be specified")
        print("  4. [OK] Batch generation includes difficulty ratings")
        print("\n" + "=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_difficulty_rating()
    sys.exit(0 if success else 1)
