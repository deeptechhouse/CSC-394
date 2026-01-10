"""
LLM client for interacting with Together.ai API.
"""
import json
import ast
import requests
from typing import Dict, Any, Optional
from config import settings


class LLMClient:
    """Client for interacting with Together.ai LLM API."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Together.ai API key (defaults to settings)
            model: Model name to use (defaults to settings)
        """
        self.api_key = api_key or settings.together_api_key
        self.api_url = settings.together_api_url
        self.model = model or settings.together_model
        
        if not self.api_key:
            raise ValueError("Together.ai API key is required. Set TOGETHER_API_KEY environment variable.")
    
    def _call_api(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Call the Together.ai API with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text from the LLM
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            
            # Better error handling to see what the API is actually saying
            if not response.ok:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_detail = response.text
                raise Exception(f"Together.ai API error ({response.status_code}): {error_detail}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Together.ai API: {str(e)}")
    
    def _extract_python_dict(self, response_text: str) -> Dict[str, Any]:
        """
        Extract Python dictionary from LLM response.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed Python dictionary
        """
        import re
        
        # Try to find dictionary in the response
        original_text = response_text
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Extract content between code blocks
            lines = response_text.split("\n")
            start_idx = 0
            end_idx = len(lines)
            
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start_idx == 0:
                        start_idx = i + 1
                    else:
                        end_idx = i
                        break
            
            response_text = "\n".join(lines[start_idx:end_idx]).strip()
        
        # Method 1: Try to parse as Python literal (handles single quotes, etc.)
        try:
            result = ast.literal_eval(response_text)
            if isinstance(result, dict):
                return result
        except (ValueError, SyntaxError) as e:
            pass
        
        # Method 2: Try JSON parsing (requires double quotes)
        try:
            result = json.loads(response_text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        # Method 3: Try to find and extract dictionary from text (more robust regex)
        # This pattern matches nested dictionaries better
        dict_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(dict_pattern, response_text, re.DOTALL)
        if matches:
            # Try each match, starting with the longest (most likely to be complete)
            matches_sorted = sorted(matches, key=len, reverse=True)
            for match in matches_sorted:
                try:
                    # Try Python literal eval first
                    result = ast.literal_eval(match)
                    if isinstance(result, dict):
                        return result
                except (ValueError, SyntaxError):
                    try:
                        # Try JSON as fallback
                        result = json.loads(match)
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        continue
        
        # Method 4: Try to fix common JSON issues and retry
        # Replace single quotes with double quotes (but be careful with strings)
        try:
            # Only replace single quotes that are clearly not in strings
            fixed_text = response_text.replace("'", '"')
            # Fix Python None, True, False to JSON equivalents
            fixed_text = fixed_text.replace('None', 'null')
            fixed_text = fixed_text.replace('True', 'true')
            fixed_text = fixed_text.replace('False', 'false')
            result = json.loads(fixed_text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        # Method 5: Try to extract just the first complete dictionary
        # Find the first { and try to match it with the last }
        first_brace = response_text.find('{')
        if first_brace != -1:
            # Count braces to find the matching closing brace
            brace_count = 0
            for i in range(first_brace, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found matching closing brace
                        dict_str = response_text[first_brace:i+1]
                        try:
                            result = ast.literal_eval(dict_str)
                            if isinstance(result, dict):
                                return result
                        except (ValueError, SyntaxError):
                            try:
                                result = json.loads(dict_str.replace("'", '"').replace('None', 'null').replace('True', 'true').replace('False', 'false'))
                                if isinstance(result, dict):
                                    return result
                            except json.JSONDecodeError:
                                pass
                        break
        
        # If all else fails, return a helpful error dict instead of raising
        # This prevents the 'str' object has no attribute 'get' error
        # Log the raw response for debugging (first 1000 chars)
        error_preview = original_text[:1000] if len(original_text) > 1000 else original_text
        
        # Try to print debug info if in debug mode (for troubleshooting)
        if settings.debug:
            print(f"\n[DEBUG] Failed to parse LLM response:")
            print(f"Response length: {len(original_text)} characters")
            print(f"First 500 chars: {original_text[:500]}")
            print(f"Last 200 chars: {original_text[-200:]}")
        
        return {
            "error": "Could not parse LLM response as dictionary",
            "raw_response": error_preview,
            "total_points_awarded": 0.0,
            "total_points_possible": 100.0,
            "percentage": 0.0,
            "state": "Error",
            "explanation": {
                "overall_feedback": f"Error: Could not parse AI grading response. The AI may have returned an invalid format. Please try submitting your response again.",
                "criterion_grades": [],
                "strengths": [],
                "weaknesses": ["Unable to parse AI grading response - format error"],
                "suggestions": ["Please try resubmitting your response", "If the problem persists, contact support"]
            }
        }
    
    def generate_question(self, prompt: str) -> Dict[str, Any]:
        """
        Generate an exam question using the LLM.
        
        Args:
            prompt: Formatted question generation prompt
            
        Returns:
            Dictionary containing question data
        """
        # Increase max_tokens to ensure complete response
        response = self._call_api(prompt, temperature=0.8, max_tokens=3000)
        return self._extract_python_dict(response)
    
    def grade_response(self, prompt: str) -> Dict[str, Any]:
        """
        Grade a student response using the LLM.
        
        Args:
            prompt: Formatted grading prompt
            
        Returns:
            Dictionary containing grading results
        """
        # Increase max_tokens for grading to ensure complete response
        response = self._call_api(prompt, temperature=0.3, max_tokens=3000)
        result = self._extract_python_dict(response)
        
        # Ensure we always return a dict
        if not isinstance(result, dict):
            return {
                "error": "LLM response was not a dictionary",
                "raw_response": str(result)[:500],
                "total_points_awarded": 0.0,
                "total_points_possible": 100.0,
                "percentage": 0.0,
                "state": "Error",
                "explanation": {
                    "overall_feedback": "Error: LLM response format was invalid",
                    "criterion_grades": [],
                    "strengths": [],
                    "weaknesses": ["Unable to process AI grading response"],
                    "suggestions": []
                }
            }
        return result
