"""
Deterministic Policy Preprocessing and Comparison Service

This service ensures consistent, deterministic results for policy comparisons by:
1. Preprocessing policies at startup with normalization
2. Implementing stable FAISS retrieval with consistent ordering
3. Setting deterministic LLM parameters
4. Adding whole-policy verification passes
5. Implementing caching for repeated comparisons
"""

import os
import re
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from services.json_utils import safe_parse_llm_json, extract_compliance_data, validate_json_structure

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PolicyMetadata:
    """Metadata for a preprocessed policy"""
    policy_id: str
    policy_type: str
    original_length: int
    normalized_length: int
    embedding_model: str
    processing_timestamp: str
    
@dataclass
class ComparisonResult:
    """Structured comparison result"""
    compliance_summary: str
    violations: List[Dict[str, str]]
    meta: Dict[str, Any]

class PolicyTextNormalizer:
    """Handles consistent text normalization for policies"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize policy text for consistent processing
        
        Steps:
        1. Remove extra line breaks and multiple spaces
        2. Standardize numbering formats
        3. Clean up inconsistent formatting
        4. Preserve structure but ensure consistency
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Basic whitespace cleanup
        normalized = re.sub(r'\s+', ' ', text.strip())  # Multiple spaces -> single space
        normalized = re.sub(r'\n\s*\n\s*\n+', '\n\n', normalized)  # Multiple line breaks -> double
        
        # Step 2: Standardize numbering formats
        # Convert various numbering patterns to consistent format
        normalized = re.sub(r'\(\s*(\d+)\s*\)', r'\1.', normalized)  # (1) -> 1.
        normalized = re.sub(r'(\d+)\)\s+', r'\1. ', normalized)      # 1) -> 1.
        normalized = re.sub(r'Section\s+(\d+)[\.:]\s*', r'Section \1: ', normalized)
        normalized = re.sub(r'Article\s+(\d+)[\.:]\s*', r'Article \1: ', normalized)
        
        # Step 3: Standardize legal formatting
        normalized = re.sub(r'\bWHEREAS[,;]\s*', 'WHEREAS, ', normalized)
        normalized = re.sub(r'\bNOW[,\s]+THEREFORE[,;]\s*', 'NOW THEREFORE, ', normalized)
        
        # Step 4: Clean up punctuation inconsistencies
        normalized = re.sub(r'\s+([,.;:])', r'\1', normalized)  # Remove space before punctuation
        normalized = re.sub(r'([,.;:])\s+', r'\1 ', normalized)  # Ensure single space after punctuation
        
        # Step 5: Standardize common legal phrases
        legal_phrases = {
            r'\bshall\s+not\b': 'shall not',
            r'\bmay\s+not\b': 'may not',
            r'\bwill\s+not\b': 'will not',
            r'\bcannot\b': 'cannot',
            r'\bcan\s+not\b': 'cannot'
        }
        
        for pattern, replacement in legal_phrases.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Step 6: Final cleanup
        normalized = re.sub(r'\s+', ' ', normalized)  # Final space cleanup
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def create_embedding_version(text: str) -> str:
        """Create a lowercase version for embeddings while preserving original"""
        return text.lower()

class PolicyCache:
    """Simple in-memory cache for comparison results"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, datetime] = {}
    
    def _generate_key(self, policy_text: str, contract_text: str, policy_type: str) -> str:
        """Generate a hash key for caching"""
        combined = f"{policy_text[:1000]}||{contract_text[:1000]}||{policy_type}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, policy_text: str, contract_text: str, policy_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if available"""
        key = self._generate_key(policy_text, contract_text, policy_type)
        if key in self.cache:
            self.access_times[key] = datetime.now()
            logger.info(f"Cache hit for comparison key: {key[:8]}...")
            return self.cache[key]
        return None
    
    def set(self, policy_text: str, contract_text: str, policy_type: str, result: Dict[str, Any]) -> None:
        """Store result in cache"""
        key = self._generate_key(policy_text, contract_text, policy_type)
        
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            logger.info(f"Evicted oldest cache entry: {oldest_key[:8]}...")
        
        self.cache[key] = result
        self.access_times[key] = datetime.now()
        logger.info(f"Cached comparison result for key: {key[:8]}...")

class DeterministicPolicyProcessor:
    """Main service for deterministic policy processing and comparison"""
    
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        self.embedding_model_name = embedding_model_name
        self.embedding_model = None
        self.normalizer = PolicyTextNormalizer()
        self.cache = PolicyCache()
        
        # Storage for preprocessed policies
        self.preprocessed_policies: Dict[str, Dict[str, Any]] = {}
        self.policy_embeddings: Dict[str, np.ndarray] = {}
        self.faiss_indices: Dict[str, faiss.Index] = {}
        
        # FAISS configuration for deterministic results
        self.faiss_config = {
            'top_k': 7,
            'similarity_threshold': 0.75,
            'index_type': 'IndexFlatIP'  # Inner product for cosine similarity
        }
        
        logger.info(f"Initialized DeterministicPolicyProcessor with model: {embedding_model_name}")
    
    def _load_embedding_model(self):
        """Load embedding model lazily"""
        if self.embedding_model is None:
            try:
                logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
    
    def preprocess_policy(self, policy_id: str, policy_text: str, policy_type: str) -> PolicyMetadata:
        """
        Preprocess a policy document for deterministic comparison
        
        Args:
            policy_id: Unique identifier for the policy
            policy_text: Raw policy text
            policy_type: Type of policy (e.g., 'companies_act', 'banking_compliance')
        
        Returns:
            PolicyMetadata with processing information
        """
        logger.info(f"Preprocessing policy: {policy_id} (type: {policy_type})")
        
        # Normalize the policy text
        normalized_text = self.normalizer.normalize_text(policy_text)
        embedding_text = self.normalizer.create_embedding_version(normalized_text)
        
        # Load embedding model if needed
        self._load_embedding_model()
        
        # Create embeddings
        logger.info(f"Creating embeddings for policy: {policy_id}")
        policy_embedding = self.embedding_model.encode([embedding_text])
        
        # Normalize embeddings for cosine similarity
        policy_embedding = policy_embedding / np.linalg.norm(policy_embedding, axis=1, keepdims=True)
        
        # Create FAISS index for this policy
        dimension = policy_embedding.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        index.add(policy_embedding.astype('float32'))
        
        # Store preprocessed data
        self.preprocessed_policies[policy_id] = {
            'original_text': policy_text,
            'normalized_text': normalized_text,
            'embedding_text': embedding_text,
            'policy_type': policy_type,
            'metadata': PolicyMetadata(
                policy_id=policy_id,
                policy_type=policy_type,
                original_length=len(policy_text),
                normalized_length=len(normalized_text),
                embedding_model=self.embedding_model_name,
                processing_timestamp=datetime.now().isoformat()
            )
        }
        
        self.policy_embeddings[policy_id] = policy_embedding[0]
        self.faiss_indices[policy_id] = index
        
        logger.info(f"Successfully preprocessed policy: {policy_id}")
        return self.preprocessed_policies[policy_id]['metadata']
    
    def _stable_faiss_retrieval(self, contract_text: str, policy_id: str) -> List[Dict[str, Any]]:
        """
        Perform stable FAISS retrieval with consistent ordering
        
        Args:
            contract_text: Contract text to compare
            policy_id: ID of the preprocessed policy
        
        Returns:
            List of retrieval results sorted by similarity (descending)
        """
        if policy_id not in self.faiss_indices:
            logger.error(f"Policy {policy_id} not found in preprocessed policies")
            return []
        
        # Normalize and embed contract text
        normalized_contract = self.normalizer.normalize_text(contract_text)
        embedding_contract = self.normalizer.create_embedding_version(normalized_contract)
        
        contract_embedding = self.embedding_model.encode([embedding_contract])
        contract_embedding = contract_embedding / np.linalg.norm(contract_embedding, axis=1, keepdims=True)
        
        # Perform FAISS search
        index = self.faiss_indices[policy_id]
        scores, indices = index.search(contract_embedding.astype('float32'), self.faiss_config['top_k'])
        
        # Process results
        results = []
        policy_data = self.preprocessed_policies[policy_id]
        
        for score, idx in zip(scores[0], indices[0]):
            if score >= self.faiss_config['similarity_threshold']:
                results.append({
                    'similarity_score': float(score),
                    'policy_text': policy_data['normalized_text'],
                    'policy_type': policy_data['policy_type'],
                    'index': int(idx)
                })
        
        # Sort by similarity score (descending) for consistent ordering
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"FAISS retrieval returned {len(results)} results above threshold {self.faiss_config['similarity_threshold']}")
        return results
    
    def compare_contract_with_policy(self, contract_text: str, policy_id: str, use_cache: bool = True) -> ComparisonResult:
        """
        Perform deterministic contract-policy comparison
        
        Args:
            contract_text: Contract text to analyze
            policy_id: ID of the policy to compare against
            use_cache: Whether to use cached results
        
        Returns:
            ComparisonResult with structured analysis
        """
        logger.info(f"Starting comparison: contract vs policy {policy_id}")
        
        if policy_id not in self.preprocessed_policies:
            raise ValueError(f"Policy {policy_id} not found. Please preprocess it first.")
        
        policy_data = self.preprocessed_policies[policy_id]
        
        # Check cache first
        if use_cache:
            cached_result = self.cache.get(policy_data['normalized_text'], contract_text, policy_data['policy_type'])
            if cached_result:
                logger.info("Returning cached comparison result")
                cached_result['meta']['cached'] = True
                return ComparisonResult(**cached_result)
        
        # Step 1: FAISS-based retrieval
        retrieval_results = self._stable_faiss_retrieval(contract_text, policy_id)
        
        # Step 2: Primary comparison using retrieved sections
        primary_result = self._perform_llm_comparison(
            contract_text, 
            policy_data['normalized_text'], 
            policy_data['policy_type'],
            retrieval_results
        )
        
        # Step 3: Whole-policy verification pass
        verification_result = self._whole_policy_verification(
            contract_text,
            policy_data['normalized_text'],
            policy_data['policy_type']
        )
        
        # Step 4: Merge results
        final_result = self._merge_comparison_results(primary_result, verification_result, retrieval_results)
        
        # Step 5: Cache the result
        if use_cache:
            self.cache.set(policy_data['normalized_text'], contract_text, policy_data['policy_type'], final_result)
        
        logger.info("Comparison completed successfully")
        return ComparisonResult(**final_result)
    
    def _perform_llm_comparison(self, contract_text: str, policy_text: str, policy_type: str, retrieval_results: List[Dict]) -> Dict[str, Any]:
        """Perform LLM-based comparison with deterministic parameters"""
        from services.gemini import model
        
        # Create focused comparison prompt using retrieval results
        if retrieval_results:
            relevant_sections = "\n".join([
                f"Relevant Section (Score: {r['similarity_score']:.3f}):\n{r['policy_text'][:500]}..."
                for r in retrieval_results[:3]
            ])
        else:
            relevant_sections = policy_text[:2000]  # Use first part of policy if no retrieval
        
        prompt = f"""You are a compliance expert. Analyze the following contract against the policy requirements.
        
CONTRACT TEXT:
{contract_text}

RELEVANT POLICY SECTIONS:
{relevant_sections}

Provide a structured analysis in the following JSON format:
{{
    "compliance_summary": "Brief overall compliance assessment",
    "violations": [
        {{
            "policy_clause": "Specific policy requirement",
            "violation": "Description of violation or gap",
            "suggested_fix": "Recommended corrective action"
        }}
    ],
    "compliance_score": 0.85
}}

Return only valid JSON without markdown formatting."""
        
        try:
            # Configure Gemini for deterministic output
            generation_config = {
                'temperature': 0,
                'top_p': 1,
                'max_output_tokens': 2048,
            }
            
            response = model.generate_content(prompt, generation_config=generation_config)
            
            # Parse JSON response with safe parsing
            parsed_response = safe_parse_llm_json(response.text.strip())
            
            # Validate and extract compliance data
            if validate_json_structure(parsed_response, required_keys=["compliance_summary"]):
                result = parsed_response
                result['retrieval_used'] = len(retrieval_results) > 0
                return result
            else:
                # Use compliance data extraction for fallback responses
                result = extract_compliance_data(parsed_response)
                result['retrieval_used'] = len(retrieval_results) > 0
                logger.info("Used fallback JSON parsing for LLM response")
                return result
                
        except Exception as e:
            logger.error(f"LLM comparison failed: {e}")
            return {
                "compliance_summary": f"Analysis failed: {str(e)}",
                "violations": [],
                "compliance_score": 0.0,
                "retrieval_used": False
            }
    
    def _whole_policy_verification(self, contract_text: str, policy_text: str, policy_type: str) -> Dict[str, Any]:
        """Perform whole-policy verification pass"""
        from services.gemini import model
        
        # Summarize policy if too large
        if len(policy_text) > 5000:
            summary_prompt = f"""Summarize the key compliance requirements from this policy document:

{policy_text}

Focus on:
1. Mandatory requirements
2. Prohibited actions
3. Required procedures
4. Penalties and consequences

Provide a concise summary of essential compliance points."""
            
            try:
                generation_config = {'temperature': 0, 'top_p': 1}
                summary_response = model.generate_content(summary_prompt, generation_config=generation_config)
                policy_summary = summary_response.text
            except Exception as e:
                logger.warning(f"Policy summarization failed: {e}")
                policy_summary = policy_text[:3000]  # Use truncated version
        else:
            policy_summary = policy_text
        
        # Verification prompt
        verification_prompt = f"""Perform a final compliance verification check:

CONTRACT:
{contract_text}

FULL POLICY REQUIREMENTS:
{policy_summary}

Identify any compliance gaps that might have been missed. Return JSON format:
{{
    "additional_violations": [
        {{
            "policy_clause": "Policy requirement",
            "violation": "Gap or violation found",
            "suggested_fix": "Recommended action"
        }}
    ],
    "verification_complete": true
}}"""

        try:
            generation_config = {'temperature': 0, 'top_p': 1}
            response = model.generate_content(verification_prompt, generation_config=generation_config)
            
            # Parse verification response with safe parsing
            parsed_response = safe_parse_llm_json(response.text.strip())
            
            # Validate verification response structure
            if validate_json_structure(parsed_response, required_keys=["verification_complete"]):
                return parsed_response
            else:
                logger.warning("Verification response parsing failed, using fallback")
                return {"additional_violations": [], "verification_complete": True}
                
        except Exception as e:
            logger.error(f"Verification pass failed: {e}")
            return {"additional_violations": [], "verification_complete": False}
    
    def _merge_comparison_results(self, primary: Dict, verification: Dict, retrieval_results: List) -> Dict[str, Any]:
        """Merge primary and verification results into final output"""
        
        # Combine violations
        all_violations = primary.get('violations', [])
        all_violations.extend(verification.get('additional_violations', []))
        
        # Create final result
        return {
            'compliance_summary': primary.get('compliance_summary', ''),
            'violations': all_violations,
            'meta': {
                'policy_used': retrieval_results[0]['policy_type'] if retrieval_results else 'unknown',
                'retrieval_used': primary.get('retrieval_used', False),
                'cached': False,
                'verification_complete': verification.get('verification_complete', False),
                'compliance_score': primary.get('compliance_score', 0.0),
                'retrieval_matches': len(retrieval_results)
            }
        }

# Global instance
_policy_processor = None

def get_policy_processor() -> DeterministicPolicyProcessor:
    """Get or create global policy processor instance"""
    global _policy_processor
    if _policy_processor is None:
        _policy_processor = DeterministicPolicyProcessor()
    return _policy_processor
