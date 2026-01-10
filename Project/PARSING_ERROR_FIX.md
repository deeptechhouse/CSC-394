# LLM Response Parsing Error Fix

## Problem
User(s) were receiving the error message:
```
Overall Feedback: Could not parse LLM response as dictionary
```

This occurred when the AI (Together.ai) returned a response that couldn't be parsed as a Python dictionary.

## Root Causes
1. **LLM sometimes adds explanatory text** before or after the dictionary
2. **Markdown code blocks** wrapping the dictionary
3. **Quote style mismatches** (single vs double quotes)
4. **Incomplete responses** due to token limits
5. **Python vs JSON syntax** differences (None vs null, True vs true, etc.)

## Solutions Implemented

### 1. Enhanced Dictionary Extraction (`llm_client.py`)
Added multiple parsing methods with fallbacks:
- **Method 1**: Python `ast.literal_eval()` (handles single quotes, Python syntax)
- **Method 2**: JSON parsing (handles double quotes, JSON syntax)
- **Method 3**: Regex extraction with multiple attempts
- **Method 4**: Quote/style fixing and retry
- **Method 5**: Brace matching to extract complete dictionary

### 2. Improved Prompts (`prompts.py`)
Made instructions more explicit:
- Added **CRITICAL** section emphasizing format requirements
- Explicitly states: "Do not use markdown code blocks"
- Instructs to start with `{` and end with `}`
- Emphasizes valid Python syntax

### 3. Increased Token Limits
- Question generation: 2000 → 3000 tokens
- Grading: 2000 → 3000 tokens
- Prevents incomplete responses that cause parsing failures

### 4. Better Error Messages
- More user-friendly error messages
- Suggests retrying the submission
- Provides helpful guidance

### 5. Debug Mode Support
- When `DEBUG=True` in config, logs raw response for troubleshooting
- Helps identify parsing issues during development

## Testing
To test the fix:
1. Submit a student response
2. If parsing fails, check debug output (if DEBUG=True)
3. The system will now attempt multiple parsing methods
4. User receives a clear error message with retry suggestion

## Prevention
The enhanced parsing should handle:
- ✅ Responses with extra text before/after dictionary
- ✅ Markdown code blocks
- ✅ Single or double quotes
- ✅ Python or JSON syntax
- ✅ Incomplete responses (extracts what's available)
- ✅ Nested dictionaries

## If Error Persists
1. Check that `TOGETHER_API_KEY` is valid
2. Verify API is responding (check network/API status)
3. Enable `DEBUG=True` in `.env` to see raw responses
4. Check token limits aren't being exceeded
5. Try resubmitting the response (may be transient API issue)

## Files Modified
- `Project/llm_client.py` - Enhanced `_extract_python_dict()` method
- `Project/prompts.py` - Improved prompt instructions for both question generation and grading
