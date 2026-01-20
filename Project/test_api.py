"""
Quick test script to diagnose API response issues.
"""
from llm_client import LLMClient
from config import settings
import json

print("=" * 60)
print("API Diagnostic Test")
print("=" * 60)
print(f"API Key configured: {'Yes' if settings.together_api_key else 'No'}")
print(f"API Key length: {len(settings.together_api_key) if settings.together_api_key else 0}")
print(f"API URL: {settings.together_api_url}")
print(f"Model: {settings.together_model}")
print(f"Debug mode: {settings.debug}")
print()

try:
    client = LLMClient()
    print("[OK] LLM Client initialized successfully")
    
    # Test with a simple prompt
    print("\n" + "=" * 60)
    print("Testing API call with simple prompt...")
    print("=" * 60)
    
    test_prompt = "Return only a Python dictionary with one key 'test' and value 'success'. Example: {'test': 'success'}"
    
    print(f"\nSending prompt: {test_prompt[:100]}...")
    response = client._call_api(test_prompt, temperature=0.3, max_tokens=500)
    
    print(f"\n[OK] API call successful!")
    print(f"Response type: {type(response)}")
    print(f"Response length: {len(response)} characters")
    print(f"\nRaw response (first 500 chars):")
    print("-" * 60)
    print(response[:500])
    print("-" * 60)
    
    print(f"\nRaw response (last 200 chars):")
    print("-" * 60)
    print(response[-200:])
    print("-" * 60)
    
    # Try to parse it
    print("\n" + "=" * 60)
    print("Testing dictionary extraction...")
    print("=" * 60)
    
    result = client._extract_python_dict(response)
    print(f"[OK] Parsing successful!")
    print(f"Result type: {type(result)}")
    print(f"Result: {json.dumps(result, indent=2)[:500]}")
    
except ValueError as e:
    print(f"\n[ERROR] ValueError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
