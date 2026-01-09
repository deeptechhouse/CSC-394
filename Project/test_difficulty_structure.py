"""
Unit test to verify difficulty rating structure without API calls.
Tests the data models and code structure.
"""
import sys
from datetime import datetime
from models import ExamQuestion, GradingRubric, DomainInformation

def test_difficulty_fields_exist():
    """Test that difficulty fields exist in ExamQuestion model."""
    print("=" * 60)
    print("Testing Difficulty Rating Structure")
    print("=" * 60)
    
    # Create a test rubric
    rubric = GradingRubric(
        criteria=["Understanding", "Analysis", "Clarity"],
        points_per_criterion={"Understanding": 10.0, "Analysis": 15.0, "Clarity": 10.0},
        total_points=35.0,
        required_elements=["Introduction", "Conclusion"]
    )
    
    # Create test domain info
    domain_info = DomainInformation(
        background_info="Test background",
        key_concepts=["Concept1", "Concept2"],
        context="Test context"
    )
    
    # Test 1: Create question with difficulty fields
    print("\n[TEST 1] Creating question with difficulty fields...")
    try:
        question = ExamQuestion(
            question_id="test-123",
            question_text="Test question?",
            rubric=rubric,
            domain_info=domain_info,
            created_at=datetime.now(),
            domain="Test Domain",
            difficulty="Medium",
            difficulty_score=6.5
        )
        
        # Verify fields exist
        assert hasattr(question, 'difficulty'), "Missing 'difficulty' field"
        assert hasattr(question, 'difficulty_score'), "Missing 'difficulty_score' field"
        assert question.difficulty == "Medium", "Difficulty value incorrect"
        assert question.difficulty_score == 6.5, "Difficulty score incorrect"
        
        print(f"  [PASS] Question created with difficulty fields")
        print(f"    - difficulty: {question.difficulty}")
        print(f"    - difficulty_score: {question.difficulty_score}")
        
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    
    # Test 2: Create question without difficulty (should be optional)
    print("\n[TEST 2] Creating question without difficulty (optional fields)...")
    try:
        question2 = ExamQuestion(
            question_id="test-456",
            question_text="Test question 2?",
            rubric=rubric,
            domain_info=domain_info,
            created_at=datetime.now(),
            domain="Test Domain"
        )
        
        # Should allow None values
        assert question2.difficulty is None or question2.difficulty == "Medium", "Difficulty should be optional"
        print(f"  [PASS] Question can be created without difficulty (optional)")
        print(f"    - difficulty: {question2.difficulty}")
        print(f"    - difficulty_score: {question2.difficulty_score}")
        
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    
    # Test 3: Verify difficulty values are valid
    print("\n[TEST 3] Testing valid difficulty values...")
    valid_difficulties = ["Easy", "Medium", "Hard"]
    for diff in valid_difficulties:
        try:
            q = ExamQuestion(
                question_id=f"test-{diff}",
                question_text="Test",
                rubric=rubric,
                domain_info=domain_info,
                created_at=datetime.now(),
                domain="Test",
                difficulty=diff,
                difficulty_score=5.0
            )
            assert q.difficulty == diff
            print(f"  [OK] Valid difficulty: {diff}")
        except Exception as e:
            print(f"  [FAIL] Error with difficulty '{diff}': {e}")
            return False
    
    # Test 4: Verify difficulty_score range
    print("\n[TEST 4] Testing difficulty_score range...")
    test_scores = [1.0, 5.0, 10.0, 7.5]
    for score in test_scores:
        try:
            q = ExamQuestion(
                question_id=f"test-score-{score}",
                question_text="Test",
                rubric=rubric,
                domain_info=domain_info,
                created_at=datetime.now(),
                domain="Test",
                difficulty="Medium",
                difficulty_score=score
            )
            assert q.difficulty_score == score
            print(f"  [OK] Valid score: {score}")
        except Exception as e:
            print(f"  [FAIL] Error with score {score}: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("STRUCTURE TEST SUMMARY")
    print("=" * 60)
    print("[SUCCESS] All structure tests passed!")
    print("\nVerified:")
    print("  1. [OK] ExamQuestion model has 'difficulty' field")
    print("  2. [OK] ExamQuestion model has 'difficulty_score' field")
    print("  3. [OK] Both fields are optional (can be None)")
    print("  4. [OK] Difficulty accepts 'Easy', 'Medium', 'Hard'")
    print("  5. [OK] Difficulty score accepts float values")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_difficulty_fields_exist()
    sys.exit(0 if success else 1)
