from fastapi import APIRouter, HTTPException
from models.policy import PolicyCategory, PolicyModel, DEFAULT_POLICIES, load_policies, get_policy_file_path
from database.db import db
import os
from typing import List
from bson import ObjectId

router = APIRouter()

@router.get("/policies/", response_model=dict)
async def get_policies():
    """Get all available policies"""
    try:
        print("Fetching policies...") # Debug log
        
        # Use the utility function to load policies with refreshed metadata
        policies = load_policies()
        
        # Return the policies
        return {"policies": policies}
    except Exception as e:
        print(f"Error in get_policies: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=f"Error retrieving policies: {str(e)}")

@router.get("/policies/categories")
async def get_policy_categories():
    """Get all policy categories"""
    return {"categories": [category.value for category in PolicyCategory]}

@router.get("/policies/{category}")
async def get_policies_by_category(category: PolicyCategory):
    """Get policies by category"""
    try:
        # Filter predefined policies
        predefined = [p for p in DEFAULT_POLICIES if p["category"] == category]

        # Filter custom policies from database
        custom = []
        for doc in db['policies'].find({"category": category}):
            custom.append({
                "id": str(doc["_id"]),
                "name": doc["name"],
                "category": doc["category"],
                "description": doc.get("description", ""),
                "file_path": doc["file_path"],
                "metadata": doc.get("metadata", {})
            })

        return {"policies": predefined + custom}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving policies: {str(e)}")

@router.get("/policies/file/{policy_id}")
async def get_policy_file(policy_id: str):
    """Get policy file by ID"""
    try:
        # Use the utility function to get the policy file path
        file_path = get_policy_file_path(policy_id)
        
        if not file_path:
            # Check database for custom policies
            try:
                doc = db['policies'].find_one({"_id": ObjectId(policy_id)})
                if doc and os.path.exists(doc["file_path"]):
                    file_path = doc["file_path"]
            except Exception:
                pass
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Policy file not found")
        
        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving policy file: {str(e)}")
