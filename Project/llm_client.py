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
        # Try to find dictionary in the response
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
            
            response_text = "\n".join(lines[start_idx:end_idx])
        
        # Try to parse as Python literal
        try:
            # Use ast.literal_eval for safe evaluation
            result = ast.literal_eval(response_text)
            if isinstance(result, dict):
                return result
        except (ValueError, SyntaxError):
            pass
        
        # Try JSON parsing as fallback
        try:
            result = json.loads(response_text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        # If all else fails, try to extract dictionary using regex
        import re
        dict_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(dict_pattern, response_text, re.DOTALL)
        if matches:
            try:
                result = ast.literal_eval(matches[-1])  # Use last match
                if isinstance(result, dict):
                    return result
            except (ValueError, SyntaxError):
                pass
        
        # If we still can't parse it, return a helpful error dict instead of raising
        # This prevents the 'str' object has no attribute 'get' error
        return {
            "error": "Could not parse LLM response as dictionary",
            "raw_response": response_text[:500],
            "total_points_awarded": 0.0,
            "total_points_possible": 100.0,
            "percentage": 0.0,
            "state": "Error",
            "explanation": {
                "overall_feedback": f"Error parsing grading response. Raw response: {response_text[:200]}",
                "criterion_grades": [],
                "strengths": [],
                "weaknesses": ["Unable to parse AI grading response"],
                "suggestions": []
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
        response = self._call_api(prompt, temperature=0.8, max_tokens=2000)
        return self._extract_python_dict(response)
    
    def grade_response(self, prompt: str) -> Dict[str, Any]:
        """
        Grade a student response using the LLM.
        
        Args:
            prompt: Formatted grading prompt
            
        Returns:
            Dictionary containing grading results
        """
        response = self._call_api(prompt, temperature=0.3, max_tokens=2000)
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
