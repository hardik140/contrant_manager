from fastapi import APIRouter, UploadFile, File, HTTPException
from services.file_utils import extract_text, extract_text_legacy
from services.gemini import summarize_contract
from database.db import db
from bson import ObjectId
import tempfile
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload-contract/")
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename or '.' not in file.filename:
        raise HTTPException(status_code=400, detail="Invalid or missing filename")
    
    ext = file.filename.split('.')[-1].lower()
    if ext not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are supported.")

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(await file.read())
        file_path = tmp.name

    try:
        # Extract text from the file with metadata
        try:
            content, extraction_metadata = extract_text(file_path)
        except Exception as e:
            # Fallback to legacy extraction
            logger.warning(f"Enhanced extraction failed, falling back: {str(e)}")
            content = extract_text_legacy(file_path)
            extraction_metadata = {"extraction_method": "legacy_fallback", "ocr_used": False}
        
        if not content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the file")
        
        logger.info(f"Successfully extracted {len(content)} characters using {extraction_metadata.get('extraction_method', 'unknown')}")
        
        # Generate summary using Gemini
        summary = summarize_contract(content)

        # Store in database with extraction metadata
        doc_id = db['contracts'].insert_one({
            "filename": file.filename,
            "content": content,
            "summary": summary,
            "type": "contract",
            "extraction_metadata": extraction_metadata,
            "created_at": {"$currentDate": {"$type": "timestamp"}}
        }).inserted_id

        return {
            "id": str(doc_id), 
            "summary": summary, 
            "filename": file.filename,
            "extraction_metadata": extraction_metadata
        }
    
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)

@router.get("/contracts/")
async def get_contracts():
    """Get all contracts"""
    try:
        contracts = []
        for doc in db['contracts'].find():
            contracts.append({
                "id": str(doc["_id"]),
                "filename": doc["filename"],
                "summary": doc.get("summary", ""),
                "type": doc.get("type", "contract")
            })
        return {"contracts": contracts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving contracts: {str(e)}")

@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str):
    """Get a specific contract by ID"""
    try:
        doc = db['contracts'].find_one({"_id": ObjectId(contract_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return {
            "id": str(doc["_id"]),
            "filename": doc["filename"],
            "content": doc["content"],
            "summary": doc.get("summary", ""),
            "type": doc.get("type", "contract")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving contract: {str(e)}")

@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    """Delete a specific contract by ID"""
    try:
        result = db['contracts'].delete_one({"_id": ObjectId(contract_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return {"message": "Contract deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting contract: {str(e)}")
