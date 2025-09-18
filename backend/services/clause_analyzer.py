"""
Clause Analysis Service

This module provides functionality to:
1. Detect and extract clauses from contract documents
2. Analyze and compare contract clauses against reference clauses

Both services use LLM (Gemini API) and embedding-based approaches.
"""

import os
import re
import json
import time
import logging
import sys
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import numpy as np
from itertools import groupby
from sentence_transformers import SentenceTransformer

# Setup project paths
try:
    import path_config  # This will auto-setup paths
except ImportError:
    # Fallback path setup if path_config is not available
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    if current_dir not in sys.path:
        sys.path.append(current_dir)

try:
    from services.text_normalizer import normalize_contract_text
except ImportError:
    try:
        # Try importing from current directory
        from text_normalizer import normalize_contract_text
    except ImportError:
        # Fallback if text_normalizer is not available
        def normalize_contract_text(text):
            """Fallback normalization function"""
            return text.strip(), type('NormStats', (), {'characters_cleaned': 0, 'dates_standardized': 0})()

# Load environment variables from .env if available
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the Gemini API client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Default model
DEFAULT_MODEL = "models/gemini-1.5-flash"  # Use the appropriate Gemini model

@dataclass
class AnalysisProvenance:
    """Provenance information for clause analysis"""
    method: str  # "llm", "embedding", "rule_based"
    similarity_score: Optional[float] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    fallback_used: bool = False
    error_occurred: bool = False
    error_message: Optional[str] = None

@dataclass 
class ClauseDetectionResult:
    """Enhanced clause detection result with metadata"""
    id: int
    title: str
    text: str
    provenance: AnalysisProvenance
    extraction_method: str = "standard"
    ocr_used: bool = False

class LLMCircuitBreaker:
    """Circuit breaker for LLM calls to prevent cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def can_proceed(self) -> bool:
        """Check if LLM calls should proceed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True
    
    def record_success(self):
        """Record successful LLM call"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed LLM call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"LLM Circuit breaker opened after {self.failure_count} failures")

# Global circuit breaker
llm_circuit_breaker = LLMCircuitBreaker()

def call_llm_with_retry(model, prompt: str, max_retries: int = 3) -> Tuple[Optional[str], bool]:
    """
    Call LLM with retry logic and circuit breaker
    
    Returns:
        Tuple of (response_text, success_flag)
    """
    if not llm_circuit_breaker.can_proceed():
        logger.warning("LLM circuit breaker is open, skipping call")
        return None, False
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            llm_circuit_breaker.record_success()
            return response.text, True
        except Exception as e:
            logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:  # Last attempt
                llm_circuit_breaker.record_failure()
                return None, False
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None, False

# Create model instance
model = genai.GenerativeModel(DEFAULT_MODEL)

def analyze_clause(reference_clause: str, user_clause: str) -> Dict[str, Any]:
    """
    Analyze a user clause against a reference clause using LLM.
    
    Args:
        reference_clause: The reference or standard clause text
        user_clause: The user's clause text to be analyzed
    
    Returns:
        Dictionary with the analysis result in the format:
        {
            "status": "covered" | "partial" | "missing",
            "explanation": str,
            "suggestion": str,
            "provenance": AnalysisProvenance
        }
    """
    start_time = time.time()
    
    # Input validation
    if not reference_clause or not isinstance(reference_clause, str):
        return {
            "status": "missing", 
            "explanation": "Reference clause is missing or invalid", 
            "suggestion": "",
            "provenance": asdict(AnalysisProvenance(
                method="validation",
                error_occurred=True,
                error_message="Invalid reference clause"
            ))
        }
    
    if not user_clause or not isinstance(user_clause, str):
        return {
            "status": "missing", 
            "explanation": "User clause is missing", 
            "suggestion": "Please provide a clause to analyze",
            "provenance": asdict(AnalysisProvenance(
                method="validation",
                error_occurred=True,
                error_message="Invalid user clause"
            ))
        }
    
    # Normalize inputs
    reference_clause = reference_clause.strip()
    user_clause = user_clause.strip()
    
    if not reference_clause:
        return {
            "status": "missing", 
            "explanation": "Reference clause is empty", 
            "suggestion": "",
            "provenance": asdict(AnalysisProvenance(
                method="validation",
                error_occurred=True,
                error_message="Empty reference clause"
            ))
        }
    
    if not user_clause:
        return {
            "status": "missing", 
            "explanation": "User clause is empty", 
            "suggestion": "Please provide a non-empty clause",
            "provenance": asdict(AnalysisProvenance(
                method="validation",
                error_occurred=True,
                error_message="Empty user clause"
            ))
        }

    # Normalize text for better comparison
    try:
        norm_reference, _ = normalize_contract_text(reference_clause)
        norm_user, _ = normalize_contract_text(user_clause)
    except Exception as e:
        logger.warning(f"Text normalization failed: {str(e)}")
        norm_reference = reference_clause
        norm_user = user_clause

    # Construct prompt with clear instructions
    prompt = f"""
    As a contract analysis expert, compare the user clause against the reference clause.
    Return a JSON with the format:
    {{
        "status": "covered" | "partial" | "missing",
        "explanation": "brief explanation",
        "suggestion": "improvement if partial, otherwise empty string",
        "confidence": 0.85
    }}
    
    Decision rules:
    - "covered": user clause fully addresses intent and obligations of the reference.
    - "partial": user clause is related but weaker, incomplete, ambiguous, or missing details.
    - "missing": user clause is irrelevant or fails to address the reference.
    
    Reference clause: "{norm_reference}"
    User clause: "{norm_user}"
    
    Analyze them and respond ONLY with the JSON object, nothing else.
    """
    
    try:
        # Call LLM with retry mechanism
        response_text, success = call_llm_with_retry(model, prompt)
        processing_time = int((time.time() - start_time) * 1000)
        
        if not success or not response_text:
            # Fallback response when LLM fails
            return {
                "status": "partial",
                "explanation": "Analysis unavailable due to service error. Manual review recommended.",
                "suggestion": "Please review clauses manually or try again later.",
                "provenance": asdict(AnalysisProvenance(
                    method="fallback",
                    processing_time_ms=processing_time,
                    fallback_used=True,
                    error_occurred=True,
                    error_message="LLM service unavailable"
                ))
            }
        
        # Try to extract valid JSON from the response
        result = None
        try:
            # First try to parse the entire response
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from a code block or surrounding text
            json_match = re.search(r'```(?:json)?\s*({\s*".*})\s*```', response_text, re.DOTALL)
            if json_match:
                # Found JSON in a code block
                result = json.loads(json_match.group(1))
            else:
                # Try to find any JSON object
                json_match = re.search(r'({[^{}]*"status"[^{}]*})', response_text, re.DOTALL)
                if json_match:
                    # Found a potential JSON object
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # Last resort: return fallback response
                        raise ValueError("Could not extract valid JSON from LLM response")
                else:
                    raise ValueError("No JSON object found in LLM response")
        
        # Validate the result structure
        required_keys = ["status", "explanation", "suggestion"]
        valid_statuses = ["covered", "partial", "missing"]
        
        if not all(key in result for key in required_keys):
            # Missing required keys
            missing_keys = [key for key in required_keys if key not in result]
            raise ValueError(f"LLM response missing required keys: {missing_keys}")
        
        if result["status"] not in valid_statuses:
            # Invalid status value
            raise ValueError(f"Invalid status: {result['status']}")
        
        # Extract confidence if available
        confidence = result.get("confidence", 0.5)
        
        return {
            "status": result["status"],
            "explanation": result["explanation"],
            "suggestion": result["suggestion"],
            "provenance": asdict(AnalysisProvenance(
                method="llm",
                confidence=confidence,
                processing_time_ms=processing_time,
                model_used=DEFAULT_MODEL
            ))
        }
            
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error in analyze_clause: {str(e)}")
        processing_time = int((time.time() - start_time) * 1000)
        
        # Fallback response
        return {
            "status": "partial" if user_clause else "missing",
            "explanation": f"Analysis error: {str(e)}. Manual review recommended.",
            "suggestion": "Please try again or review clauses manually.",
            "provenance": asdict(AnalysisProvenance(
                method="fallback",
                processing_time_ms=processing_time,
                fallback_used=True,
                error_occurred=True,
                error_message=str(e)
            ))
        }


# Initialize sentence transformer model for embedding-based segmentation
try:
    # Use a smaller, faster model for embedding
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Warning: Could not load embedding model: {str(e)}")
    embedding_model = None

def detect_clauses(text: str) -> List[Dict]:
    """
    Detect and extract clauses from contract text.
    
    Args:
        text: The contract text to analyze
        
    Returns:
        List of clause dictionaries, each with:
        - id: Sequential identifier
        - title: Detected title (or empty string)
        - text: The clause text content
        - provenance: Analysis metadata
        - extraction_method: How text was extracted
        - ocr_used: Whether OCR was used
    """
    start_time = time.time()
    
    # Input validation
    if not text or not isinstance(text, str) or not text.strip():
        return []
    
    try:
        # STEP 1: Preprocessing with normalization
        normalized_text, norm_stats = normalize_contract_text(text)
        processed_text = preprocess_contract_text(normalized_text)
        
        logger.info(f"Text normalization: {norm_stats.characters_cleaned} chars cleaned, "
                   f"{norm_stats.dates_standardized} dates standardized")
        
        # STEP 2: Rule-based segmentation
        candidate_clauses = rule_based_segmentation(processed_text)
        
        # STEP 3: Embedding-based refinement (if available)
        if embedding_model is not None and len(candidate_clauses) > 1:
            refined_clauses = embedding_based_refinement(candidate_clauses)
        else:
            refined_clauses = candidate_clauses
            logger.warning("Embedding model unavailable, skipping refinement")
        
        # STEP 4: LLM enhancement for ambiguous cases
        final_clauses = enhance_clauses_with_llm(refined_clauses)
        
        # STEP 5: Format output with sequential IDs and provenance
        result = []
        processing_time = int((time.time() - start_time) * 1000)
        
        for idx, clause in enumerate(final_clauses, 1):
            # Determine extraction method confidence
            confidence = 0.9 if clause.get("title") else 0.7
            if len(clause.get("text", "").split()) < 10:
                confidence *= 0.8  # Lower confidence for very short clauses
            
            result.append({
                "id": idx,
                "title": clause.get("title", ""),
                "text": clause.get("text", "").strip(),
                "provenance": asdict(AnalysisProvenance(
                    method="hybrid",
                    confidence=confidence,
                    processing_time_ms=processing_time // len(final_clauses),
                    model_used="sentence-transformers" if embedding_model else "rule_based"
                )),
                "extraction_method": "standard",
                "ocr_used": False  # This would be set by file_utils if OCR was used
            })
        
        logger.info(f"Detected {len(result)} clauses in {processing_time}ms")
        return result
        
    except Exception as e:
        # Log the error but never crash
        logger.error(f"Error in detect_clauses: {str(e)}")
        processing_time = int((time.time() - start_time) * 1000)
        
        # Fallback: Try to extract paragraphs as clauses
        fallback_clauses = []
        try:
            # Simple paragraph-based fallback
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
            for idx, para in enumerate(paragraphs, 1):
                fallback_clauses.append({
                    "id": idx,
                    "title": "",
                    "text": para,
                    "provenance": asdict(AnalysisProvenance(
                        method="fallback",
                        confidence=0.3,
                        processing_time_ms=processing_time,
                        fallback_used=True,
                        error_occurred=True,
                        error_message=str(e)
                    )),
                    "extraction_method": "paragraph_split",
                    "ocr_used": False
                })
        except:
            # Ultimate fallback: return the whole text as one clause
            if text.strip():
                fallback_clauses = [{
                    "id": 1,
                    "title": "",
                    "text": text.strip(),
                    "provenance": asdict(AnalysisProvenance(
                        method="fallback",
                        confidence=0.1,
                        processing_time_ms=processing_time,
                        fallback_used=True,
                        error_occurred=True,
                        error_message="Complete processing failure"
                    )),
                    "extraction_method": "whole_document",
                    "ocr_used": False
                }]
                
        return fallback_clauses

def preprocess_contract_text(text: str) -> str:
    """Preprocess contract text to normalize and clean it."""
    # Split into lines for processing
    lines = text.split('\n')
    unique_lines = []
    seen_lines = set()
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and common header/footer patterns
        if not line or re.match(r'^Page \d+ of \d+$', line) or line in seen_lines:
            continue
        unique_lines.append(line)
        seen_lines.add(line)
    
    # Join lines back with newlines to preserve structure
    text = '\n'.join(unique_lines)
    
    # Remove page numbers but keep line structure
    text = re.sub(r'\b[Pp]age\s+\d+\s+(?:of|/)\s+\d+\b', '', text)
    
    # Normalize excessive whitespace within lines but keep line breaks
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text

def rule_based_segmentation(text: str) -> List[Dict]:
    """Apply rule-based segmentation to identify clause boundaries."""
    # Split text into lines for analysis
    lines = text.split('\n')
    
    # Patterns to detect clause boundaries
    section_patterns = [
        r'^\s*(\d+\.(?:\d+\.)*)\s+([A-Z][A-Za-z\s]+)',  # Numbered sections with title: "1.2 TERMINATION"
        r'^\s*([A-Z][A-Z\s]+)(:|\.|$)',                 # ALL CAPS headings: "TERMINATION:"
        r'^\s*([A-Z][a-z][A-Za-z\s]+)(:|\.|$)',         # Title Case headings: "Termination:"
        r'^\s*(?:Section|SECTION|Art\.?|Article)\s+(\d+[\.\d]*)\s*[:\-.]?\s*([A-Za-z\s]+)',  # "Section 1.2 - Termination"
        r'^\s*\(([a-zA-Z]|[ivxIVX]+)\)\s*([A-Z][A-Za-z\s]+)'  # "(a) Termination" or "(iv) Payment Terms"
    ]
    
    # Common legal clause keywords
    legal_keywords = [
        'Term', 'Termination', 'Indemnity', 'Indemnification', 'Payment', 'Confidentiality',
        'Governing Law', 'Jurisdiction', 'Warranty', 'Warranties', 'Liability', 'Force Majeure',
        'Assignment', 'Amendment', 'Insurance', 'Compliance', 'Notice', 'Dispute', 'Resolution',
        'Severability', 'Waiver', 'Intellectual Property', 'Representation', 'Covenant'
    ]
    
    # Store clauses as we find them
    clauses = []
    current_title = ""
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line matches any section heading pattern
        is_heading = False
        new_title = ""
        
        # Try regex patterns first
        for pattern in section_patterns:
            match = re.match(pattern, line)
            if match:
                is_heading = True
                if len(match.groups()) > 1:
                    # Extract section number and title
                    new_title = match.group(2).strip() if match.group(2) else match.group(1).strip()
                else:
                    new_title = match.group(1).strip()
                break
        
        # If not matched by regex, check for legal keywords
        if not is_heading:
            for keyword in legal_keywords:
                # Check if line starts with the keyword followed by colon or period
                if re.match(fr'^\s*{keyword}\s*[:\.]\s*', line, re.IGNORECASE):
                    is_heading = True
                    new_title = keyword
                    break
        
        # If this is a new heading, store the previous clause if it exists
        if is_heading and current_text:
            clauses.append({
                "title": current_title,
                "text": " ".join(current_text).strip()
            })
            current_title = new_title
            current_text = []
            # Extract text after the title in the current line
            content_after_title = re.sub(fr'^.*?{re.escape(new_title)}\s*[:\.]\s*', '', line, flags=re.IGNORECASE)
            if content_after_title:
                current_text.append(content_after_title)
        else:
            # If we're at a new heading but no previous content, just update the title
            if is_heading:
                current_title = new_title
                content_after_title = re.sub(fr'^.*?{re.escape(new_title)}\s*[:\.]\s*', '', line, flags=re.IGNORECASE)
                if content_after_title:
                    current_text.append(content_after_title)
            else:
                # Regular content line
                current_text.append(line)
    
    # Add the final clause if it exists
    if current_text:
        clauses.append({
            "title": current_title,
            "text": " ".join(current_text).strip()
        })
    
    return clauses

def embedding_based_refinement(clauses: List[Dict]) -> List[Dict]:
    """Refine clause boundaries using embedding-based semantic similarity."""
    if not clauses or embedding_model is None:
        return clauses
    
    # If we only have one clause, no refinement needed
    if len(clauses) <= 1:
        return clauses
    
    refined_clauses = []
    current_texts = []
    current_title = clauses[0]["title"]
    
    # Create embeddings for each clause
    try:
        clause_texts = [c["text"] for c in clauses]
        embeddings = embedding_model.encode(clause_texts)
        
        # Analyze semantic similarity between adjacent clauses
        for i in range(len(clauses)):
            if i == 0:
                current_texts.append(clauses[i]["text"])
                continue
            
            # Calculate cosine similarity between current and previous clause
            cosine_similarity = np.dot(embeddings[i], embeddings[i-1]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i-1])
            )
            
            # If similarity is high, merge with previous clause
            if cosine_similarity > 0.8 and not clauses[i]["title"]:
                current_texts.append(clauses[i]["text"])
            else:
                # Create a new clause with accumulated text
                refined_clauses.append({
                    "title": current_title,
                    "text": " ".join(current_texts).strip()
                })
                current_title = clauses[i]["title"]
                current_texts = [clauses[i]["text"]]
        
        # Add the last clause
        if current_texts:
            refined_clauses.append({
                "title": current_title,
                "text": " ".join(current_texts).strip()
            })
            
        return refined_clauses
        
    except Exception as e:
        print(f"Embedding refinement failed: {str(e)}")
        return clauses  # Fallback to original clauses

def enhance_clauses_with_llm(clauses: List[Dict]) -> List[Dict]:
    """Use LLM to enhance clause detection for ambiguous or untitled clauses."""
    enhanced_clauses = []
    ambiguous_sections = []
    
    # Get the full text for position reference later
    full_text = " ".join(clause["text"] for clause in clauses)
    
    # First pass: identify clauses that need enhancement
    for i, clause in enumerate(clauses):
        # Check if this is a long section with no title
        if len(clause["text"].split()) > 100 and not clause["title"]:
            ambiguous_sections.append((i, clause))
        else:
            enhanced_clauses.append(clause)
    
    # If no ambiguous sections, return original clauses
    if not ambiguous_sections:
        return clauses
    
    # Process ambiguous sections with LLM
    for i, clause in ambiguous_sections:
        try:
            # Truncate text if extremely long for API limits
            text_for_llm = clause["text"][:8000] if len(clause["text"]) > 8000 else clause["text"]
            
            prompt = f"""
            As a legal expert, analyze this contract text and split it into distinct clauses.
            For each clause, identify its title (if any) and the clause text.
            
            CONTRACT TEXT:
            {text_for_llm}
            
            Return ONLY a JSON array with objects containing "title" and "text" fields.
            If you cannot identify a title, use an empty string.
            """
            
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Try to extract JSON from the response
            try:
                # First try to parse the entire response
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from code block
                json_match = re.search(r'```(?:json)?\s*(\[.*\])\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Use original clause if we can't parse the response
                    enhanced_clauses.append(clause)
                    continue
            
            # Add extracted clauses
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and "text" in item:
                        enhanced_clauses.append({
                            "title": item.get("title", ""),
                            "text": item["text"]
                        })
            else:
                enhanced_clauses.append(clause)
                
        except Exception as e:
            print(f"LLM enhancement failed for clause: {str(e)}")
            enhanced_clauses.append(clause)  # Keep original on failure
    
    # Sort clauses by their position in the original text
    # This is a heuristic to maintain document order
    final_clauses = []
    for clause in enhanced_clauses:
        if "text" in clause and clause["text"]:
            # Find position of first few words in original text
            sample = " ".join(clause["text"].split()[:5])
            pos = full_text.find(sample)
            if pos >= 0:
                final_clauses.append((pos, clause))
            else:
                final_clauses.append((float('inf'), clause))
    
    # Sort by position and return just the clauses
    return [clause for _, clause in sorted(final_clauses, key=lambda x: x[0])]

if __name__ == "__main__":
    # Test the analyze_clause function
    reference = "The lessee must maintain valid insurance coverage for the property during the full lease period."
    user = "The tenant shall maintain insurance."
    
    result = analyze_clause(reference, user)
    print("Clause Analysis Result:")
    print(json.dumps(result, indent=2))
    
    # Test the detect_clauses function
    test_contract = """
    LEASE AGREEMENT
    
    1. Term: This lease shall be for a period of 12 months, commencing on January 1, 2025.
    
    2. Rent: Tenant agrees to pay $1,500 per month, due on the first day of each month.
    
    3. Security Deposit: Tenant shall provide a security deposit of $2,000.
    
    4. Maintenance: The tenant shall keep the premises in good repair and promptly notify landlord of any damage.
    
    5. Insurance: The tenant shall maintain insurance for the full lease period.
    
    6. Termination: Either party may terminate this agreement with 30 days written notice.
    """
    
    clauses = detect_clauses(test_contract)
    print("\nDetected Clauses:")
    print(json.dumps(clauses, indent=2))
