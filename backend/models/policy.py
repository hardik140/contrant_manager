from typing import Optional, List, Dict
from pydantic import BaseModel
from enum import Enum

class PolicyCategory(str, Enum):
    COMPANIES_ACT = "companies_act"
    BANKING = "banking"
    DATA_PROTECTION = "data_protection"
    EMPLOYMENT = "employment"
    REGULATORY = "regulatory"

class PolicyMetadata(BaseModel):
    jurisdiction: Optional[str] = None
    last_updated: Optional[str] = None
    key_areas: Optional[List[str]] = None
    regulators: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    scope: Optional[str] = None
    status: Optional[str] = "Active"
    note: Optional[str] = None

class PolicyModel(BaseModel):
    id: str
    name: str
    category: PolicyCategory
    description: str
    file_path: str
    metadata: Optional[PolicyMetadata] = None

class PolicyResponse(BaseModel):
    policies: List[PolicyModel]

def get_policy_file_path(policy_id: str) -> str:
    """Get the file path for a policy by ID"""
    import os
    
    # Check predefined policies
    for policy in DEFAULT_POLICIES:
        if policy["id"] == policy_id:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Check in policies dir first
            policies_dir = os.path.join(base_dir, "policies")
            file_name = os.path.basename(policy["file_path"])
            policy_path = os.path.join(policies_dir, file_name)
            
            if os.path.exists(policy_path):
                return policy_path
                
            # Then check in root dir
            root_path = os.path.join(base_dir, file_name)
            if os.path.exists(root_path):
                return root_path
    
    # No file found
    return ""

def load_policies() -> List[Dict]:
    """Load all policies and refresh their metadata"""
    import os
    from database.db import db
    
    # Create policies directory if it doesn't exist
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policies_dir = os.path.join(base_dir, "policies")
    os.makedirs(policies_dir, exist_ok=True)
    
    # Process predefined policies
    policies = []
    for policy in DEFAULT_POLICIES:
        policy_copy = dict(policy)
        file_name = os.path.basename(policy["file_path"])
        
        # Check both in policies dir and root dir
        policy_file_path = os.path.join(policies_dir, file_name)
        root_file_path = os.path.join(base_dir, file_name)
        
        # Initialize metadata if it doesn't exist
        if "metadata" not in policy_copy:
            policy_copy["metadata"] = {}
        
        # Check in policies directory first
        if os.path.exists(policy_file_path):
            policy_copy["metadata"]["status"] = "Active"
        # Then check in root directory
        elif os.path.exists(root_file_path):
            # Copy to policies directory
            import shutil
            shutil.copy2(root_file_path, policy_file_path)
            policy_copy["metadata"]["status"] = "Active"
        else:
            policy_copy["metadata"]["status"] = "Pending"
            policy_copy["metadata"]["note"] = "Policy file will be added soon"
        
        # Always use the policies directory for the file path
        policy_copy["file_path"] = os.path.join("policies", file_name)
        policies.append(policy_copy)
    
    # Get custom policies from database
    custom_policies = []
    try:
        for doc in db['policies'].find():
            custom_policies.append({
                "id": str(doc["_id"]),
                "name": doc["name"],
                "category": doc.get("category", "custom"),
                "description": doc.get("description", ""),
                "file_path": doc["file_path"],
                "metadata": doc.get("metadata", {})
            })
    except Exception:
        # Continue if DB access fails
        pass
        
    # Combine both types of policies
    return policies + custom_policies

# Predefined policies with descriptions
DEFAULT_POLICIES = [
    {
        "id": "companies-act-2013",
        "name": "Companies Act Compliance",
        "category": PolicyCategory.COMPANIES_ACT,
        "description": "Ensures compliance with Companies Act 2013 regulations using FAISS legal index.",
        "file_path": "LEGAL_INDEX",  # Special marker to use legal index instead of PDF
        "metadata": {
            "jurisdiction": "India",
            "last_updated": "2023-12-01",
            "key_areas": ["Corporate Governance", "Board Responsibilities", "Statutory Requirements"],
            "regulators": ["Ministry of Corporate Affairs"],
            "status": "Active",
            "source_type": "legal_index",
            "index_provisions": 948,
            "search_method": "FAISS_semantic"
        }
    },
    {
        "id": "banking-regulations",
        "name": "Banking Compliance Policy",
        "category": PolicyCategory.BANKING,
        "description": "Guidelines for banking operations and compliance.",
        "file_path": "policies/banking_regulations.pdf",
        "metadata": {
            "jurisdiction": "Global",
            "key_areas": ["Risk Management", "KYC", "Anti-Money Laundering"],
            "regulators": ["RBI", "Federal Reserve"],
            "status": "Active"
        }
    },
    {
        "id": "data-protection-gdpr",
        "name": "GDPR Compliance",
        "category": PolicyCategory.DATA_PROTECTION,
        "description": "Data protection and privacy requirements under GDPR.",
        "file_path": "policies/gdpr_compliance.pdf",
        "metadata": {
            "jurisdiction": "EU",
            "last_updated": "2023-11-15",
            "key_areas": ["Data Privacy", "User Rights", "Data Security"],
            "regulators": ["European Data Protection Board"],
            "status": "Active"
        }
    },
    {
        "id": "employment-policy",
        "name": "Employment Law Compliance",
        "category": PolicyCategory.EMPLOYMENT,
        "description": "Employment law and workplace regulations.",
        "file_path": "policies/employment_law.pdf",
        "metadata": {
            "jurisdiction": "US",
            "key_areas": ["Labor Laws", "Workplace Safety", "Employee Rights"],
            "status": "Pending",
            "note": "Updated policy coming soon with 2025 regulations"
        }
    }
]
