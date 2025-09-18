"""
JSON Utilities for LLM Response Parsing

This module provides utilities for safely parsing JSON from LLM responses,
which often contain formatting issues like markdown fences, trailing commas,
or extra text that makes them invalid JSON.
"""

import json
import re
import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

def safe_parse_llm_json(response: str) -> Dict[str, Any]:
    """
    Parse LLM response into JSON safely, repairing common issues.
    
    LLMs often return JSON with formatting problems:
    - Wrapped in ```json markdown fences
    - Trailing commas before } or ]
    - Extra whitespace and newlines
    - Additional text before/after JSON
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed JSON as dictionary, or {"fallback": original_text} if parsing fails
    """
    if not response or not response.strip():
        logger.warning("Empty response provided to safe_parse_llm_json")
        return {"fallback": ""}
    
    original_response = response.strip()
    
    # Step 1: Try parsing original response first
    try:
        parsed = json.loads(original_response)
        logger.debug("Successfully parsed original LLM response as JSON")
        return parsed
    except json.JSONDecodeError as e:
        logger.debug(f"Initial JSON parsing failed: {e}")
    
    # Step 2: Clean the response and try again
    try:
        cleaned = _clean_llm_response(original_response)
        parsed = json.loads(cleaned)
        logger.debug("Successfully parsed cleaned LLM response as JSON")
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse cleaned LLM response as JSON: {e}")
    
    # Step 3: Try extracting JSON from response
    try:
        extracted_json = _extract_json_from_text(original_response)
        if extracted_json:
            parsed = json.loads(extracted_json)
            logger.debug("Successfully extracted and parsed JSON from LLM response")
            return parsed
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse extracted JSON: {e}")
    
    # Step 4: Final fallback - return original response wrapped
    logger.warning("All JSON parsing attempts failed, using fallback")
    return {"fallback": original_response}

def _clean_llm_response(response: str) -> str:
    """
    Clean LLM response by removing common formatting issues.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned response string
    """
    # Remove markdown code fences
    cleaned = re.sub(r'```json\s*', '', response)
    cleaned = re.sub(r'```\s*$', '', cleaned)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    
    # Remove trailing commas before closing braces/brackets
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    
    # Collapse multiple whitespaces and newlines
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def _extract_json_from_text(text: str) -> Union[str, None]:
    """
    Try to extract JSON object from text that might contain additional content.
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    # Look for JSON object patterns
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested objects
        r'\{.*?\}',  # Basic object pattern
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            # Try to parse each match
            try:
                json.loads(match.strip())
                return match.strip()
            except json.JSONDecodeError:
                continue
    
    return None

def validate_json_structure(data: Dict[str, Any], required_keys: list = None) -> bool:
    """
    Validate that parsed JSON has expected structure.
    
    Args:
        data: Parsed JSON data
        required_keys: List of required keys to check for
        
    Returns:
        True if structure is valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    # If this is a fallback response, consider it invalid structure
    if "fallback" in data and len(data) == 1:
        return False
    
    # Check for required keys if specified
    if required_keys:
        for key in required_keys:
            if key not in data:
                logger.debug(f"Required key '{key}' missing from JSON structure")
                return False
    
    return True

def extract_compliance_data(parsed_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract compliance-related data from parsed JSON with fallback handling.
    
    Args:
        parsed_json: Parsed JSON response from LLM
        
    Returns:
        Dictionary with compliance data
    """
    # Handle fallback case
    if "fallback" in parsed_json:
        return {
            "compliance_summary": parsed_json["fallback"],
            "violations": [],
            "compliance_score": 0.5,  # Default score for unparseable responses
            "source": "fallback_parsing"
        }
    
    # Extract standard compliance fields
    return {
        "compliance_summary": parsed_json.get("compliance_summary", "No summary available"),
        "violations": parsed_json.get("violations", []),
        "compliance_score": parsed_json.get("compliance_score", 0.0),
        "recommendations": parsed_json.get("recommendations", []),
        "source": "structured_parsing"
    }

# Example usage and testing
if __name__ == "__main__":
    # Test cases for the JSON parser
    test_cases = [
        # Valid JSON
        '{"compliance_score": 0.8, "violations": []}',
        
        # JSON with markdown fences
        '```json\n{"compliance_score": 0.8, "violations": []}\n```',
        
        # JSON with trailing comma
        '{"compliance_score": 0.8, "violations": [],}',
        
        # JSON with extra text
        'Here is the analysis: {"compliance_score": 0.8, "violations": []} That completes the review.',
        
        # Invalid JSON
        'This is not valid JSON at all',
        
        # Empty response
        '',
    ]
    
    print("Testing safe_parse_llm_json function:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case[:50]}{'...' if len(test_case) > 50 else ''}")
        result = safe_parse_llm_json(test_case)
        print(f"Result: {result}")
        is_valid = validate_json_structure(result, ["compliance_score"])
        print(f"Valid structure: {is_valid}")
