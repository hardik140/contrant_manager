"""
Policy Startup Service

This service handles preprocessing of all policies at backend startup
to ensure deterministic and consistent results for all comparisons.
"""

import os
import logging
from typing import Dict, List, Any
from services.deterministic_policy_processor import get_policy_processor, PolicyMetadata
from services.file_utils import extract_text
from models.policy import DEFAULT_POLICIES

logger = logging.getLogger(__name__)

class PolicyStartupService:
    """Service to preprocess policies at backend startup"""
    
    def __init__(self):
        self.processor = get_policy_processor()
        self.initialization_complete = False
        self.processed_policies: Dict[str, PolicyMetadata] = {}
    
    async def initialize_policies(self) -> Dict[str, PolicyMetadata]:
        """
        Initialize and preprocess all policies at startup
        
        Returns:
            Dictionary of policy_id -> PolicyMetadata for successfully processed policies
        """
        logger.info("Starting policy preprocessing at backend startup...")
        
        processed_count = 0
        failed_count = 0
        
        for policy_config in DEFAULT_POLICIES:
            try:
                policy_id = policy_config['id']
                policy_name = policy_config['name']
                policy_type = policy_config.get('category', 'unknown')
                file_path = policy_config['file_path']
                
                logger.info(f"Processing policy: {policy_name} (ID: {policy_id})")
                
                # Handle special case for legal index
                if file_path == "LEGAL_INDEX":
                    logger.info(f"Policy {policy_id} uses legal index - creating synthetic policy text")
                    policy_text = self._create_legal_index_policy_text(policy_config)
                else:
                    # Extract text from policy file
                    policy_text = self._extract_policy_text(file_path)
                
                if policy_text:
                    # Preprocess the policy
                    metadata = self.processor.preprocess_policy(
                        policy_id=policy_id,
                        policy_text=policy_text,
                        policy_type=str(policy_type)
                    )
                    
                    self.processed_policies[policy_id] = metadata
                    processed_count += 1
                    logger.info(f"✅ Successfully processed policy: {policy_name}")
                else:
                    logger.error(f"❌ Failed to extract text for policy: {policy_name}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing policy {policy_config.get('name', 'unknown')}: {e}")
                failed_count += 1
        
        self.initialization_complete = True
        
        logger.info(f"Policy preprocessing complete: {processed_count} successful, {failed_count} failed")
        
        if processed_count == 0:
            logger.warning("⚠️  No policies were successfully processed!")
        
        return self.processed_policies
    
    def _extract_policy_text(self, file_path: str) -> str:
        """
        Extract text from a policy file with multiple location attempts
        
        Args:
            file_path: Path to the policy file
            
        Returns:
            Extracted policy text or empty string if failed
        """
        # Try multiple locations for the policy file
        possible_paths = [
            file_path,  # Original path
            os.path.join("policies", file_path),  # In policies directory
            os.path.join("backend", "policies", file_path),  # In backend/policies
            os.path.join("..", file_path),  # Parent directory
            os.path.join("..", "policies", file_path),  # Parent policies directory
        ]
        
        for attempt_path in possible_paths:
            if os.path.exists(attempt_path):
                try:
                    logger.info(f"Extracting text from: {attempt_path}")
                    text, metadata = extract_text(attempt_path)
                    
                    if text and text.strip():
                        logger.info(f"Successfully extracted {len(text)} characters from {attempt_path}")
                        return text
                    else:
                        logger.warning(f"Extracted empty text from {attempt_path}")
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text from {attempt_path}: {e}")
                    continue
        
        logger.error(f"Could not find or extract text from policy file: {file_path}")
        return ""
    
    def _create_legal_index_policy_text(self, policy_config: Dict[str, Any]) -> str:
        """
        Create synthetic policy text for legal index-based policies
        
        Args:
            policy_config: Policy configuration from DEFAULT_POLICIES
            
        Returns:
            Synthetic policy text for processing
        """
        policy_name = policy_config.get('name', 'Unknown Policy')
        description = policy_config.get('description', 'Legal compliance policy')
        metadata = policy_config.get('metadata', {})
        
        # Create comprehensive policy text based on the legal index
        policy_text = f"""
{policy_name}

POLICY OVERVIEW:
{description}

This policy is based on the Indian Contract Act legal provisions and ensures compliance with statutory requirements for contract formation, performance, and termination.

KEY AREAS OF COMPLIANCE:
"""
        
        # Add key areas from metadata
        key_areas = metadata.get('key_areas', [])
        for area in key_areas:
            policy_text += f"\n- {area}: All contracts must comply with {area.lower()} requirements as specified in the Indian Contract Act."
        
        # Add regulatory information
        regulators = metadata.get('regulators', [])
        if regulators:
            policy_text += f"\n\nREGULATORY OVERSIGHT:\nThis policy is governed by: {', '.join(regulators)}"
        
        # Add standard contract requirements
        policy_text += """

MANDATORY REQUIREMENTS:

1. CONTRACT FORMATION:
   - All contracts must have clear offer, acceptance, and consideration
   - Parties must have legal capacity to enter into agreements
   - Contracts must be for lawful purposes only

2. PERFORMANCE OBLIGATIONS:
   - All parties must perform their obligations as specified
   - Time is of the essence unless otherwise stated
   - Performance must comply with applicable legal standards

3. TERMINATION PROVISIONS:
   - Contracts must include clear termination clauses
   - Notice requirements must be specified
   - Consequences of breach must be outlined

4. DISPUTE RESOLUTION:
   - Governing law must be clearly specified
   - Dispute resolution mechanisms should be included
   - Jurisdiction for legal proceedings must be defined

5. COMPLIANCE MONITORING:
   - Regular review of contract terms for legal compliance
   - Documentation of all material changes
   - Maintenance of audit trails for contractual obligations

PROHIBITED PRACTICES:
- Contracts that violate statutory provisions
- Agreements that lack essential elements
- Terms that are unconscionable or against public policy
- Clauses that attempt to exclude liability for fraud or willful default

This policy ensures all contractual arrangements comply with Indian Contract Act provisions and related statutory requirements.
"""
        
        logger.info(f"Created synthetic policy text for {policy_name}: {len(policy_text)} characters")
        return policy_text
    
    def get_processed_policy_summary(self) -> Dict[str, Any]:
        """
        Get summary of processed policies
        
        Returns:
            Summary information about processed policies
        """
        if not self.initialization_complete:
            return {
                "status": "not_initialized",
                "processed_count": 0,
                "policies": []
            }
        
        policies_info = []
        for policy_id, metadata in self.processed_policies.items():
            policies_info.append({
                "policy_id": policy_id,
                "policy_type": metadata.policy_type,
                "normalized_length": metadata.normalized_length,
                "processing_timestamp": metadata.processing_timestamp
            })
        
        return {
            "status": "initialized",
            "processed_count": len(self.processed_policies),
            "policies": policies_info,
            "embedding_model": self.processed_policies[list(self.processed_policies.keys())[0]].embedding_model if self.processed_policies else None
        }
    
    def is_policy_available(self, policy_id: str) -> bool:
        """Check if a policy is available for comparison"""
        return policy_id in self.processed_policies

# Global instance
_startup_service = None

def get_startup_service() -> PolicyStartupService:
    """Get or create global startup service instance"""
    global _startup_service
    if _startup_service is None:
        _startup_service = PolicyStartupService()
    return _startup_service
