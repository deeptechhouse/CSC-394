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
            
        Raises:
            ValueError: If API key is missing or invalid
            Exception: If API call fails
        """
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("Together.ai API key is required. Please set TOGETHER_API_KEY environment variable or create a .env file with your API key.")
        
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
                    # Try to extract a meaningful error message
                    if isinstance(error_data, dict):
                        if "error" in error_data:
                            error_obj = error_data["error"]
                            if isinstance(error_obj, dict):
                                error_detail = error_obj.get("message", str(error_obj))
                            else:
                                error_detail = str(error_obj)
                        else:
                            error_detail = str(error_data)
                    else:
                        error_detail = str(error_data)
                except:
                    error_detail = response.text[:500]  # Limit error text length
                
                # Provide helpful error messages based on status code
                if response.status_code == 401:
                    raise ValueError(f"API authentication failed. Please check your TOGETHER_API_KEY is correct. Error: {error_detail}")
                elif response.status_code == 429:
                    raise Exception(f"API rate limit exceeded. Please try again later. Error: {error_detail}")
                else:
                    raise Exception(f"Together.ai API error (HTTP {response.status_code}): {error_detail}")
            
            result = response.json()
            
            # Check if response has the expected structure
            if "choices" not in result or not result["choices"]:
                raise Exception(f"Unexpected API response format: {list(result.keys())}")
            
            content = result["choices"][0]["message"]["content"]
            if not content or content.strip() == "":
                raise Exception("API returned empty response. Please try again.")
            
            return content
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except requests.exceptions.Timeout:
            raise Exception("API request timed out. The service may be slow or unavailable. Please try again.")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Together.ai API. Please check your internet connection.")
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
        
        # Method 0: Try to remove any leading/trailing explanatory text
        # Look for common patterns like "Here is...", "Sure, here is...", etc.
        intro_patterns = [
            r'^(Here is|Sure, here is|Here\'s|Sure, here\'s|I\'ll|I will|Let me|The dictionary|The response).*?(\{.*)',
            r'^(.*?)(\{.*)',
        ]
        for pattern in intro_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match and len(match.groups()) >= 2:
                response_text = match.group(2)
                break
        
        # Remove markdown code blocks if present (improved detection)
        if "```" in response_text:
            # Try to extract content between code blocks
            code_block_pattern = r'```(?:python|json)?\s*\n?(.*?)```'
            matches = re.findall(code_block_pattern, response_text, re.DOTALL | re.IGNORECASE)
            if matches:
                # Use the longest match (most likely to be complete)
                response_text = max(matches, key=len).strip()
            else:
                # Fallback: remove lines with ``` markers
                lines = response_text.split("\n")
                start_idx = 0
                end_idx = len(lines)
                
                for i, line in enumerate(lines):
                    if "```" in line:
                        if start_idx == 0:
                            start_idx = i + 1
                        else:
                            end_idx = i
                            break
                
                if start_idx > 0 and end_idx < len(lines):
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
                                # Try with quote and value fixes
                                fixed_dict = dict_str.replace("'", '"').replace('None', 'null').replace('True', 'true').replace('False', 'false')
                                result = json.loads(fixed_dict)
                                if isinstance(result, dict):
                                    return result
                            except json.JSONDecodeError:
                                pass
                        break
        
        # Method 6: Try to find dictionary by looking for key patterns
        # Look for common keys that should be in the response
        common_keys = ['total_points_awarded', 'total_points_possible', 'percentage', 'state', 'explanation', 
                       'question_text', 'background_info', 'key_concepts', 'rubric', 'difficulty']
        for key in common_keys:
            key_pattern = rf'["\']?{key}["\']?\s*[:=]'
            match = re.search(key_pattern, response_text, re.IGNORECASE)
            if match:
                # Found a key, try to extract dictionary starting from before this key
                start_pos = max(0, match.start() - 50)
                # Find the opening brace before this position
                brace_pos = response_text.rfind('{', 0, match.start())
                if brace_pos != -1:
                    # Try to extract from this brace
                    brace_count = 0
                    for i in range(brace_pos, len(response_text)):
                        if response_text[i] == '{':
                            brace_count += 1
                        elif response_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                dict_str = response_text[brace_pos:i+1]
                                try:
                                    result = ast.literal_eval(dict_str)
                                    if isinstance(result, dict):
                                        return result
                                except (ValueError, SyntaxError):
                                    try:
                                        fixed_dict = dict_str.replace("'", '"').replace('None', 'null').replace('True', 'true').replace('False', 'false')
                                        result = json.loads(fixed_dict)
                                        if isinstance(result, dict):
                                            return result
                                    except json.JSONDecodeError:
                                        pass
                                break
                break
        
        # If all else fails, return a helpful error dict instead of raising
        # This prevents the 'str' object has no attribute 'get' error
        # Log the raw response for debugging (first 1000 chars)
        error_preview = original_text[:1000] if len(original_text) > 1000 else original_text
        
        # Clean up error preview - remove any prompt fragments that might confuse users
        # Look for common prompt fragments and remove them
        prompt_fragments = [
            " and end with the closing brace",
            "Start your response directly with the opening brace",
            "Do not use markdown code blocks",
            "CRITICAL:",
        ]
        for fragment in prompt_fragments:
            if fragment in error_preview:
                # Try to clean up the preview - remove text before/after the fragment
                idx = error_preview.find(fragment)
                if idx > 0:
                    # Keep content before the fragment
                    error_preview = error_preview[:idx].strip()
        
        # Try to print debug info if in debug mode (for troubleshooting)
        if settings.debug:
            print(f"\n[DEBUG] =========================================")
            print(f"[DEBUG] FAILED TO PARSE LLM RESPONSE")
            print(f"[DEBUG] =========================================")
            print(f"[DEBUG] Response length: {len(original_text)} characters")
            print(f"[DEBUG] Full response:")
            print(f"[DEBUG] {original_text}")
            print(f"[DEBUG] =========================================")
            print(f"[DEBUG] Attempting to extract dictionary...")
            # Try to show where the issue might be
            if '{' in original_text:
                first_brace = original_text.find('{')
                print(f"[DEBUG] First '{{' found at position {first_brace}")
                print(f"[DEBUG] Text before first brace: {repr(original_text[:first_brace])}")
            if '}' in original_text:
                last_brace = original_text.rfind('}')
                print(f"[DEBUG] Last '}}' found at position {last_brace}")
                print(f"[DEBUG] Text after last brace: {repr(original_text[last_brace+1:])}")
        
        return {
            "error": "Could not parse LLM response as dictionary. The AI returned an invalid format.",
            "raw_response": error_preview,
            "total_points_awarded": 0.0,
            "total_points_possible": 100.0,
            "percentage": 0.0,
            "state": "Error",
            "explanation": {
                "overall_feedback": "Error: Could not parse AI response. The AI may have returned an invalid format. Please try submitting your response again.",
                "criterion_grades": [],
                "strengths": [],
                "weaknesses": ["Unable to parse AI response - format error"],
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
            
        Raises:
            ValueError: If the response cannot be parsed or contains an error
        """
        try:
            # Increase max_tokens to ensure complete response
            response = self._call_api(prompt, temperature=0.8, max_tokens=3000)
            
            # Log the raw response for debugging
            if settings.debug:
                print(f"\n[DEBUG] Raw API response received:")
                print(f"[DEBUG] Length: {len(response)} characters")
                print(f"[DEBUG] First 1000 chars:\n{response[:1000]}")
                print(f"[DEBUG] Last 500 chars:\n{response[-500:]}")
                print(f"[DEBUG] " + "="*60)
            
            result = self._extract_python_dict(response)
            
            # Validate that result is a dictionary
            if not isinstance(result, dict):
                # Log the actual response for debugging
                if settings.debug:
                    print(f"[DEBUG] LLM returned non-dict response: {type(result).__name__}")
                    print(f"[DEBUG] Response content (first 500 chars): {str(result)[:500]}")
                raise ValueError(f"LLM response could not be parsed as a dictionary. Got type: {type(result).__name__}. Please check your API key and try again.")
            
            # Check if result contains an error
            if "error" in result:
                error_msg = result.get("error", "Unknown parsing error")
                raw_response = result.get("raw_response", "")
                
                # Log debug info if enabled
                if settings.debug and raw_response:
                    print(f"[DEBUG] Parsing error: {error_msg}")
                    print(f"[DEBUG] Raw response preview: {raw_response[:500]}")
                
                # Clean up any prompt text fragments that might have leaked into the error message
                if "closing brace" in error_msg.lower() or "' and end with" in error_msg:
                    error_msg = "Could not parse AI response. The AI returned an invalid format. This may indicate: 1) API key issue, 2) API returned unexpected format, or 3) Network issue. Please check your configuration and try again."
                elif "Could not parse" not in error_msg:
                    error_msg = f"Failed to parse AI response: {error_msg}"
                
                raise ValueError(error_msg)
            
            return result
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            # Wrap other exceptions in a clearer error message
            raise ValueError(f"Failed to generate question: {str(e)}")
    
    def grade_response(self, prompt: str) -> Dict[str, Any]:
        """
        Grade a student response using the LLM.
        
        Args:
            prompt: Formatted grading prompt
            
        Returns:
            Dictionary containing grading results
            
        Raises:
            ValueError: If the response cannot be parsed or contains an error
        """
        try:
            # Increase max_tokens for grading to ensure complete response
            response = self._call_api(prompt, temperature=0.3, max_tokens=3000)
            
            # Log the raw response for debugging
            if settings.debug:
                print(f"\n[DEBUG] Raw grading API response received:")
                print(f"[DEBUG] Length: {len(response)} characters")
                print(f"[DEBUG] First 1000 chars:\n{response[:1000]}")
                print(f"[DEBUG] Last 500 chars:\n{response[-500:]}")
                print(f"[DEBUG] " + "="*60)
            
            result = self._extract_python_dict(response)
            
            # Validate that result is a dictionary
            if not isinstance(result, dict):
                if settings.debug:
                    print(f"[DEBUG] Grading response was not a dict: {type(result).__name__}")
                    print(f"[DEBUG] Response content (first 500 chars): {str(result)[:500]}")
                raise ValueError(f"LLM grading response could not be parsed as a dictionary. Got type: {type(result).__name__}")
            
            # Check if result contains an error
            if "error" in result:
                error_msg = result.get("error", "Unknown parsing error")
                # Clean up any prompt text fragments that might have leaked into the error message
                if "closing brace" in error_msg.lower() or "' and end with" in error_msg:
                    error_msg = "Could not parse AI grading response. The AI returned an invalid format. This may indicate: 1) API issue, 2) Unexpected response format, or 3) Network issue. Please try again."
                elif "Could not parse" not in error_msg:
                    error_msg = f"Failed to parse AI grading response: {error_msg}"
                
                raise ValueError(error_msg)
            
            return result
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            # Wrap other exceptions in a clearer error message
            raise ValueError(f"Failed to grade response: {str(e)}")
