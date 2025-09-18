#!/usr/bin/env python3
"""
Enhanced Clause Analyzer with Legal Index Integration

This module integrates the FAISS-based legal document index with clause analysis
to provide more accurate and legally-grounded clause detection and analysis.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from build_legal_index import LegalSearchEngine
except ImportError:
    # Fallback if build_legal_index is not available
    LegalSearchEngine = None

from services.clause_analyzer import AnalysisProvenance, call_llm_with_retry
from services.gemini import model

logger = logging.getLogger(__name__)

class EnhancedClauseAnalyzer:
    """Enhanced clause analyzer with legal index integration"""
    
    def __init__(self, legal_index_dir: str = "./index"):
        """
        Initialize enhanced analyzer with legal index
        
        Args:
            legal_index_dir: Path to the legal document index
        """
        self.legal_search_engine = None
        self.legal_index_available = False
        
        # Try to load legal index
        if LegalSearchEngine and os.path.exists(legal_index_dir):
            try:
                self.legal_search_engine = LegalSearchEngine(legal_index_dir)
                self.legal_search_engine.load_index()
                self.legal_index_available = True
                logger.info(f"✅ Loaded legal index with {len(self.legal_search_engine.sections)} sections")
            except Exception as e:
                logger.warning(f"Could not load legal index: {e}")
                self.legal_index_available = False
        else:
            logger.info("Legal index not available, using standard clause detection")
    
    def detect_clauses_with_legal_context(self, text: str) -> List[Dict[str, Any]]:
        """
        Enhanced clause detection that uses legal index for better accuracy
        
        Args:
            text: Contract text to analyze
            
        Returns:
            List of detected clauses with legal context
        """
        start_time = time.time()
        
        # Input validation
        if not text or not isinstance(text, str) or not text.strip():
            logger.warning("Empty or invalid text provided for clause detection")
            return []
        
        logger.info(f"Starting enhanced clause detection for text of length: {len(text)}")
        
        # Step 1: Use standard pattern-based detection
        standard_clauses = self._detect_clauses_standard(text)
        
        # Step 2: If legal index is available, enhance with legal context
        if self.legal_index_available:
            enhanced_clauses = self._enhance_clauses_with_legal_context(standard_clauses, text)
        else:
            enhanced_clauses = standard_clauses
        
        # Step 3: Add provenance information
        processing_time = int((time.time() - start_time) * 1000)
        
        for clause in enhanced_clauses:
            if 'provenance' not in clause:
                clause['provenance'] = asdict(AnalysisProvenance(
                    method="enhanced_detection" if self.legal_index_available else "standard_detection",
                    processing_time_ms=processing_time,
                    model_used="FAISS+all-mpnet-base-v2" if self.legal_index_available else "pattern_based",
                    fallback_used=not self.legal_index_available
                ))
        
        logger.info(f"Enhanced clause detection completed: {len(enhanced_clauses)} clauses found in {processing_time}ms")
        return enhanced_clauses
    
    def _detect_clauses_standard(self, text: str) -> List[Dict[str, Any]]:
        """Standard pattern-based clause detection"""
        clauses = []
        
        # Split text into potential clauses using common patterns
        patterns = [
            r'^\d+\.\s+(.+?)(?=^\d+\.\s+|\Z)',  # Numbered clauses
            r'^[A-Z][^.]+:\s*(.+?)(?=^[A-Z][^.]+:|\Z)',  # Title-based clauses
            r'^\([a-z]\)\s+(.+?)(?=^\([a-z]\)|\Z)',  # Lettered clauses
        ]
        
        lines = text.split('\n')
        current_clause = None
        clause_buffer = []
        clause_id = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new clause
            if self._is_clause_start(line):
                # Save previous clause
                if current_clause and clause_buffer:
                    clauses.append({
                        "id": clause_id,
                        "title": current_clause,
                        "text": ' '.join(clause_buffer).strip(),
                        "extraction_method": "pattern_based",
                        "ocr_used": False
                    })
                    clause_id += 1
                
                # Start new clause
                current_clause = self._extract_clause_title(line)
                clause_buffer = [line]
            else:
                # Continue current clause
                if clause_buffer:
                    clause_buffer.append(line)
        
        # Add the last clause
        if current_clause and clause_buffer:
            clauses.append({
                "id": clause_id,
                "title": current_clause,
                "text": ' '.join(clause_buffer).strip(),
                "extraction_method": "pattern_based",
                "ocr_used": False
            })
        
        return clauses
    
    def _is_clause_start(self, line: str) -> bool:
        """Check if a line starts a new clause"""
        import re
        patterns = [
            r'^\d+\.\s+',  # "1. "
            r'^[A-Z][A-Z\s]+:\s*',  # "PAYMENT TERMS:"
            r'^\([a-z]\)\s+',  # "(a) "
            r'^Article\s+\d+',  # "Article 1"
            r'^Section\s+\d+',  # "Section 1"
        ]
        
        return any(re.match(pattern, line) for pattern in patterns)
    
    def _extract_clause_title(self, line: str) -> str:
        """Extract clause title from the line"""
        import re
        
        # Try different title extraction patterns
        patterns = [
            r'^\d+\.\s+(.+?)(?:\.|$)',  # "1. Payment Terms."
            r'^([A-Z][A-Z\s]+):\s*',    # "PAYMENT TERMS:"
            r'^\([a-z]\)\s+(.+?)(?:\.|$)',  # "(a) Definitions."
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        
        # Fallback: take first few words
        words = line.split()[:5]
        return ' '.join(words)
    
    def _enhance_clauses_with_legal_context(self, clauses: List[Dict], contract_text: str) -> List[Dict]:
        """Enhance clauses with legal context from the legal index"""
        enhanced_clauses = []
        
        for clause in clauses:
            enhanced_clause = clause.copy()
            
            # Search for relevant legal provisions
            legal_context = self._find_legal_context(clause['text'])
            enhanced_clause['legal_context'] = legal_context
            
            # Add legal relevance score
            if legal_context:
                max_score = max(ctx['similarity_score'] for ctx in legal_context)
                enhanced_clause['legal_relevance_score'] = max_score
            else:
                enhanced_clause['legal_relevance_score'] = 0.0
            
            # Enhanced title if legal context provides better description
            if legal_context and legal_context[0]['similarity_score'] > 0.7:
                legal_title = legal_context[0]['title']
                if len(legal_title) > len(clause['title']):
                    enhanced_clause['enhanced_title'] = legal_title
            
            enhanced_clauses.append(enhanced_clause)
        
        return enhanced_clauses
    
    def _find_legal_context(self, clause_text: str) -> List[Dict]:
        """Find relevant legal provisions for a clause"""
        if not self.legal_search_engine:
            return []
        
        try:
            # Search for relevant legal provisions
            results = self.legal_search_engine.search(
                clause_text,
                top_k=3,
                min_score=0.4
            )
            
            # Format results for clause context
            legal_context = []
            for result in results:
                legal_context.append({
                    "provision_id": result['id'],
                    "title": result['title'],
                    "text": result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
                    "section_type": result['section_type'],
                    "chapter": result.get('chapter', ''),
                    "similarity_score": result['similarity_score']
                })
            
            return legal_context
            
        except Exception as e:
            logger.warning(f"Error finding legal context: {e}")
            return []
    
    def analyze_clause_with_legal_reference(self, user_clause: str, reference_clause: str = None) -> Dict[str, Any]:
        """
        Enhanced clause analysis using legal index as reference
        
        Args:
            user_clause: The clause to analyze
            reference_clause: Optional reference clause (if not provided, uses legal index)
            
        Returns:
            Analysis result with legal context
        """
        start_time = time.time()
        
        # If no reference clause provided, find the most relevant legal provision
        if not reference_clause and self.legal_index_available:
            legal_results = self.legal_search_engine.search(user_clause, top_k=1, min_score=0.3)
            if legal_results:
                reference_clause = legal_results[0]['text']
                reference_source = legal_results[0]['title']
            else:
                reference_clause = "No specific legal provision found. General contract law principles apply."
                reference_source = "General Contract Law"
        elif not reference_clause:
            reference_clause = "Standard contract clause analysis."
            reference_source = "Standard Analysis"
        else:
            reference_source = "User Provided"
        
        # Perform the analysis using the enhanced reference
        analysis_result = self._perform_enhanced_clause_analysis(user_clause, reference_clause)
        
        # Add legal context and provenance
        processing_time = int((time.time() - start_time) * 1000)
        
        analysis_result.update({
            "reference_source": reference_source,
            "legal_context": self._find_legal_context(user_clause) if self.legal_index_available else [],
            "provenance": asdict(AnalysisProvenance(
                method="enhanced_legal_analysis" if self.legal_index_available else "standard_analysis",
                processing_time_ms=processing_time,
                model_used="FAISS+Gemini" if self.legal_index_available else "Gemini",
                confidence=analysis_result.get('confidence', 0.5)
            ))
        })
        
        return analysis_result
    
    def _perform_enhanced_clause_analysis(self, user_clause: str, reference_clause: str) -> Dict[str, Any]:
        """Perform enhanced analysis with legal reference"""
        
        prompt = f"""
        As a legal contract analysis expert, analyze the user clause against the reference provision.
        
        Reference Legal Provision: "{reference_clause}"
        
        User Clause: "{user_clause}"
        
        Provide analysis in JSON format:
        {{
            "status": "covered" | "partial" | "missing" | "non_compliant",
            "explanation": "detailed explanation of the analysis",
            "suggestion": "specific improvement suggestions or empty string if fully covered",
            "confidence": 0.0-1.0,
            "legal_risk_level": "low" | "medium" | "high",
            "compliance_notes": "specific compliance observations"
        }}
        
        Analysis rules:
        - "covered": User clause fully aligns with legal requirements
        - "partial": Clause is relevant but may have gaps or weaknesses  
        - "missing": Clause doesn't address the legal requirement
        - "non_compliant": Clause may violate legal principles
        
        Focus on legal compliance, clarity, and enforceability.
        Respond ONLY with the JSON object.
        """
        
        try:
            response_text, success = call_llm_with_retry(model, prompt)
            
            if not success or not response_text:
                return {
                    "status": "partial",
                    "explanation": "Analysis unavailable due to service error. Manual legal review recommended.",
                    "suggestion": "Please consult with a legal professional for detailed analysis.",
                    "confidence": 0.1,
                    "legal_risk_level": "medium",
                    "compliance_notes": "Automated analysis failed"
                }
            
            # Parse JSON response
            import json
            import re
            
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'```(?:json)?\s*({\s*".*})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Fallback parsing
                    result = {
                        "status": "partial",
                        "explanation": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                        "suggestion": "Review response for detailed analysis.",
                        "confidence": 0.5,
                        "legal_risk_level": "medium",
                        "compliance_notes": "Manual parsing required"
                    }
            
            # Ensure required fields
            required_fields = ["status", "explanation", "suggestion", "confidence"]
            for field in required_fields:
                if field not in result:
                    result[field] = "Not specified" if field != "confidence" else 0.5
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced clause analysis: {e}")
            return {
                "status": "partial", 
                "explanation": f"Analysis error: {str(e)}",
                "suggestion": "Manual review recommended due to analysis error.",
                "confidence": 0.1,
                "legal_risk_level": "high",
                "compliance_notes": "Error in automated analysis"
            }

# Global enhanced analyzer instance
_enhanced_analyzer = None

def get_enhanced_analyzer() -> EnhancedClauseAnalyzer:
    """Get singleton instance of enhanced analyzer"""
    global _enhanced_analyzer
    if _enhanced_analyzer is None:
        _enhanced_analyzer = EnhancedClauseAnalyzer()
    return _enhanced_analyzer

# Enhanced API functions that replace the old ones
def detect_clauses_enhanced(text: str) -> List[Dict]:
    """
    Enhanced clause detection using legal index
    
    Args:
        text: Contract text to analyze
        
    Returns:
        List of detected clauses with legal context
    """
    analyzer = get_enhanced_analyzer()
    return analyzer.detect_clauses_with_legal_context(text)

def analyze_clause_enhanced(reference_clause: str, user_clause: str) -> Dict[str, Any]:
    """
    Enhanced clause analysis using legal index
    
    Args:
        reference_clause: Reference clause (can be empty to use legal index)
        user_clause: User clause to analyze
        
    Returns:
        Analysis result with legal context
    """
    analyzer = get_enhanced_analyzer()
    return analyzer.analyze_clause_with_legal_reference(user_clause, reference_clause)

if __name__ == "__main__":
    # Test the enhanced analyzer
    test_contract = """
    1. PAYMENT TERMS: Payment shall be made within 30 days of invoice date.
    2. TERMINATION: Either party may terminate this agreement with written notice.
    3. CONFIDENTIALITY: Both parties agree to maintain confidential information.
    """
    
    analyzer = EnhancedClauseAnalyzer()
    
    print("🔍 Testing Enhanced Clause Detection...")
    clauses = analyzer.detect_clauses_with_legal_context(test_contract)
    
    for clause in clauses:
        print(f"\nClause {clause['id']}: {clause['title']}")
        print(f"Text: {clause['text'][:100]}...")
        if 'legal_context' in clause and clause['legal_context']:
            print(f"Legal Context: {clause['legal_context'][0]['title']} (Score: {clause['legal_context'][0]['similarity_score']:.3f})")
        print(f"Legal Relevance: {clause.get('legal_relevance_score', 0.0):.3f}")
    
    print("\n🔍 Testing Enhanced Clause Analysis...")
    analysis = analyzer.analyze_clause_with_legal_reference(
        "Payment shall be made within 30 days of invoice date."
    )
    print(f"Analysis Status: {analysis['status']}")
    print(f"Legal Risk: {analysis.get('legal_risk_level', 'unknown')}")
    print(f"Explanation: {analysis['explanation'][:100]}...")
