from fastapi import APIRouter, UploadFile, File, HTTPException
from services.file_utils import extract_text
from services.gemini import compare_with_policy
from database.db import db
from bson import ObjectId
import tempfile
import os

router = APIRouter()

@router.post("/compare/")
async def compare_contract_policy(contract: UploadFile = File(...), policy: UploadFile = File(...)):
    # Validate file formats
    for file in [contract, policy]:
        if not file.filename or '.' not in file.filename:
            raise HTTPException(status_code=400, detail=f"Invalid filename: {file.filename}")
        
        ext = file.filename.split('.')[-1].lower()
        if ext not in ["pdf", "docx"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file format for {file.filename}. Only PDF and DOCX are supported.")

    # Create temporary files
    contract_path = None
    policy_path = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp1, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp2:
            tmp1.write(await contract.read())
            tmp2.write(await policy.read())
            contract_path = tmp1.name
            policy_path = tmp2.name

        # Extract text from both files
        contract_text = extract_text(contract_path)
        policy_text = extract_text(policy_path)
        
        if not contract_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from contract file")
        
        if not policy_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from policy file")

        # Compare using Gemini
        comparison_result = compare_with_policy(contract_text, policy_text)

        # Store in database
        comparison_doc = {
            "contract_filename": contract.filename,
            "policy_filename": policy.filename,
            "contract_text": contract_text,
            "policy_text": policy_text,
            "result": comparison_result,
            "type": "comparison"
        }
        
        doc_id = db['comparisons'].insert_one(comparison_doc).inserted_id

        return {
            "id": str(doc_id),
            "comparison": comparison_result,
            "contract_filename": contract.filename,
            "policy_filename": policy.filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing comparison: {str(e)}")
    
    finally:
        # Clean up temporary files
        for path in [contract_path, policy_path]:
            if path and os.path.exists(path):
                os.unlink(path)

@router.get("/comparisons/")
async def get_comparisons():
    """Get all comparisons"""
    try:
        comparisons = []
        for doc in db['comparisons'].find():
            comparisons.append({
                "id": str(doc["_id"]),
                "contract_filename": doc["contract_filename"],
                "policy_filename": doc["policy_filename"],
                "result": doc.get("result", ""),
                "type": doc.get("type", "comparison")
            })
        return {"comparisons": comparisons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving comparisons: {str(e)}")

@router.get("/comparisons/{comparison_id}")
async def get_comparison(comparison_id: str):
    """Get a specific comparison by ID"""
    try:
        doc = db['comparisons'].find_one({"_id": ObjectId(comparison_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Comparison not found")
        
        return {
            "id": str(doc["_id"]),
            "contract_filename": doc["contract_filename"],
            "policy_filename": doc["policy_filename"],
            "contract_text": doc["contract_text"],
            "policy_text": doc["policy_text"],
            "result": doc.get("result", ""),
            "type": doc.get("type", "comparison")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving comparison: {str(e)}")

@router.delete("/comparisons/{comparison_id}")
async def delete_comparison(comparison_id: str):
    """Delete a specific comparison by ID"""
    try:
        result = db['comparisons'].delete_one({"_id": ObjectId(comparison_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Comparison not found")
        
        return {"message": "Comparison deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting comparison: {str(e)}")
