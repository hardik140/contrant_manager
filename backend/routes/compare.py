from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.file_utils import extract_text
from services.gemini import compare_with_policy
from services.enhanced_clause_analyzer import get_enhanced_analyzer
from services.deterministic_policy_processor import get_policy_processor
from services.policy_startup_service import get_startup_service
from database.db import db
from models.policy import DEFAULT_POLICIES
from bson import ObjectId
import tempfile
import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

def compare_with_deterministic_processor(contract_text: str, policy_id: str) -> dict:
    """
    Deterministic comparison using the new policy processor
    
    This ensures consistent results through:
    1. Normalized text processing
    2. Stable FAISS retrieval with consistent ordering  
    3. Deterministic LLM parameters
    4. Whole-policy verification
    5. Caching for identical requests
    """
    try:
        logger.info(f"Starting deterministic comparison for policy: {policy_id}")
        
        # Get the processor and startup service
        processor = get_policy_processor()
        startup_service = get_startup_service()
        
        # Check if policy is available
        if not startup_service.is_policy_available(policy_id):
            logger.error(f"Policy {policy_id} not available in preprocessed policies")
            return None
        
        # Perform deterministic comparison
        result = processor.compare_contract_with_policy(
            contract_text=contract_text,
            policy_id=policy_id,
            use_cache=True
        )
        
        # Convert result to dictionary format
        result_dict = {
            'compliance_analysis': {
                'compliance_summary': result.compliance_summary,
                'violations': result.violations
            },
            'analysis_metrics': {
                'compliance_score': result.meta.get('compliance_score', 0.0),
                'retrieval_matches': result.meta.get('retrieval_matches', 0)
            },
            'full_report': result.compliance_summary,
            'meta': result.meta
        }
        
        logger.info(f"Deterministic comparison completed for policy: {policy_id}")
        return result_dict
        
    except Exception as e:
        logger.error(f"Error in deterministic comparison: {e}")
        return None

def compare_with_legal_index(contract_text: str, policy_id: str) -> dict:
    """
    Deterministic comparison using the new policy processor
    
    This ensures consistent results through:
    1. Normalized text processing
    2. Stable FAISS retrieval with consistent ordering  
    3. Deterministic LLM parameters
    4. Whole-policy verification
    5. Caching for identical requests
    """
    try:
        logger.info(f"Starting deterministic comparison for policy: {policy_id}")
        
        # Get the processor and startup service
        processor = get_policy_processor()
        startup_service = get_startup_service()
        
        # Check if policy is available
        if not startup_service.is_policy_available(policy_id):
            logger.error(f"Policy {policy_id} not available in preprocessed policies")
            return None
        
        # Perform deterministic comparison
        result = processor.compare_contract_with_policy(
            contract_text=contract_text,
            policy_id=policy_id,
            use_cache=True
        )
        
        # Convert result to dictionary format
        result_dict = {
            'compliance_analysis': {
                'compliance_summary': result.compliance_summary,
                'violations': result.violations
            },
            'analysis_metrics': {
                'compliance_score': result.meta.get('compliance_score', 0.0),
                'retrieval_matches': result.meta.get('retrieval_matches', 0)
            },
            'full_report': result.compliance_summary,
            'meta': result.meta
        }
        
        logger.info(f"Deterministic comparison completed for policy: {policy_id}")
        return result_dict
        
    except Exception as e:
        logger.error(f"Error in deterministic comparison: {e}")
        return None
    """
    Enhanced comparison using legal index instead of PDF extraction
    """
    try:
        # Get the enhanced analyzer with legal index
        analyzer = get_enhanced_analyzer()
        
        if not analyzer.legal_index_available:
            # Fallback to traditional PDF-based comparison
            return None
            
        # Use the legal index to find relevant provisions for comparison
        legal_results = analyzer.legal_search_engine.search(
            contract_text, 
            top_k=10,  # Get more results for comprehensive comparison
            min_score=0.3
        )
        
        if not legal_results:
            return None
            
        # Combine the top legal provisions as "policy text"
        policy_provisions = []
        for result in legal_results:
            policy_provisions.append({
                "provision": result['text'],
                "title": result['title'],
                "section": result.get('section_type', ''),
                "similarity": result['similarity_score']
            })
        
        # Create a consolidated policy text from legal provisions
        policy_text = "\n\n".join([
            f"**{provision['title']}** (Similarity: {provision['similarity']:.3f})\n{provision['provision']}"
            for provision in policy_provisions[:5]  # Use top 5 provisions
        ])
        
        # Perform comparison using the legal provisions
        comparison_result = compare_with_policy(contract_text, policy_text)
        
        # Enhance the result with legal context
        if isinstance(comparison_result, dict):
            comparison_result['legal_provisions_used'] = policy_provisions
            comparison_result['legal_index_used'] = True
            comparison_result['policy_source'] = 'Indian Contract Act Legal Index'
        
        return comparison_result
        
    except Exception as e:
        print(f"Error in legal index comparison: {e}")
        return None

@router.post("/compare/")
async def compare_contract_policy(contract: UploadFile = File(...), policy_id: str = Form(...)):
    # Validate contract file format
    if not contract.filename or '.' not in contract.filename:
        raise HTTPException(status_code=400, detail=f"Invalid filename: {contract.filename}")
    
    ext = contract.filename.split('.')[-1].lower()
    if ext not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format for {contract.filename}. Only PDF and DOCX are supported.")

    # Find policy by ID
    policy_file_path = None
    policy_filename = None
    
    print(f"Looking for policy with ID: {policy_id}")
    
    # First check predefined policies
    for policy in DEFAULT_POLICIES:
        if policy["id"] == policy_id:
            # Check if this policy uses the legal index instead of a file
            if policy["file_path"] == "LEGAL_INDEX":
                policy_file_path = "LEGAL_INDEX"
                policy_filename = "LEGAL_INDEX"
                print(f"Policy {policy_id} will use legal index instead of file")
                break
            
            policy_filename = os.path.basename(policy["file_path"])
            
            # First check if it's directly in the policies directory
            policies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policies")
            policy_file_path = os.path.join(policies_dir, policy_filename)
            
            print(f"Checking policy path: {policy_file_path}")
            
            # If not in policies directory, check root directory
            if not os.path.exists(policy_file_path):
                root_policy_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), 
                    policy_filename
                )
                print(f"Checking root policy path: {root_policy_path}")
                
                if os.path.exists(root_policy_path):
                    policy_file_path = root_policy_path
                    print(f"Found policy at: {policy_file_path}")
                else:
                    # Try to locate any PDF files that might match
                    print(f"Policy file not found at expected locations. Searching for PDF files...")
                    for root, _, files in os.walk(os.path.dirname(os.path.dirname(__file__))):
                        for file in files:
                            if file.endswith('.pdf'):
                                print(f"Found PDF file: {os.path.join(root, file)}")
                                
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Policy file not found for ID: {policy_id}"
                    )
            else:
                print(f"Found policy at: {policy_file_path}")
            break
    
    # If not found in predefined policies, check database
    if not policy_file_path:
        try:
            doc = db['policies'].find_one({"_id": ObjectId(policy_id)})
            if doc:
                policy_file_path = doc["file_path"]
                policy_filename = os.path.basename(policy_file_path)
                if not os.path.exists(policy_file_path):
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Policy file not found for ID: {policy_id}"
                    )
        except Exception as e:
            pass  # Continue to check next options
            
    # If still not found, return error
    if not policy_file_path or not policy_filename:
        raise HTTPException(
            status_code=404, 
            detail=f"Policy not found for ID: {policy_id}"
        )
            
    # Create temporary files
    contract_path = None
    
    try:
        # Use the correct suffix based on the actual file extension
        file_ext = contract.filename.split('.')[-1].lower()
        
        # Ensure extension is one we can handle
        if file_ext not in ['pdf', 'docx']:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension: .{file_ext}. Only PDF and DOCX are supported."
            )
            
        suffix = f".{file_ext}"
        
        # Create a named temporary file with the correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp1:
            content = await contract.read()
            # Check if content is empty
            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )
            tmp1.write(content)
            contract_path = tmp1.name
        
        print(f"Created temporary file: {contract_path} with extension {suffix}")

        print(f"Contract path: {contract_path}, Policy path: {policy_file_path}")
        
        # Special handling for policy files (only for actual PDF files)
        if policy_file_path != "LEGAL_INDEX" and policy_file_path.endswith('.pdf'):
            root_policy_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                policy_filename
            )
            if os.path.exists(root_policy_path) and root_policy_path != policy_file_path:
                print(f"Found original policy file at {root_policy_path}, using it instead")
                policy_file_path = root_policy_path
        
        # Extract text from contract file
        try:
            contract_text, contract_metadata = extract_text(contract_path)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to extract text from contract file: {str(e)}"
            )
            
        if not contract_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from contract file")

        # Check if this policy should use legal index
        use_legal_index = (
            policy_file_path == "LEGAL_INDEX" or
            policy_filename == "A187209.pdf" or 
            policy_id == "companies-act-2013" or
            (policy_file_path and "A187209" in policy_file_path)
        )
        
        # Try deterministic processor first for consistent results
        comparison_result = compare_with_deterministic_processor(contract_text, policy_id)
        
        if comparison_result is None:
            # Fallback to original methods
            if use_legal_index:
                print(f"Deterministic processor failed, using legal index for policy comparison")
                # Use enhanced comparison with legal index
                comparison_result = compare_with_legal_index(contract_text, policy_id)
                
                if comparison_result is None:
                    # Fallback to PDF extraction if legal index fails
                    print(f"Legal index comparison failed, falling back to PDF extraction")
                    try:
                        policy_text, policy_metadata = extract_text(policy_file_path)
                        if not policy_text.strip():
                            raise HTTPException(status_code=400, detail="Could not extract text from policy file")
                        comparison_result = compare_with_policy(contract_text, policy_text)
                    except Exception as e:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Failed to extract text from policy file: {str(e)}"
                        )
                else:
                    # Set policy_text for database storage when using legal index
                    policy_text = "LEGAL_INDEX_USED - See legal_provisions_used in result"
                    policy_metadata = {
                        "source": "Legal Index",
                        "method": "FAISS_semantic_search",
                        "provisions_count": len(comparison_result.get('legal_provisions_used', [])),
                        "index_type": "Indian Contract Act"
                    }
            else:
                # Use traditional PDF extraction for other policies
                print(f"Deterministic processor failed, using traditional PDF extraction")
                try:
                    policy_text, policy_metadata = extract_text(policy_file_path)
                except Exception as e:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to extract text from policy file: {str(e)}"
                    )
                
                if not policy_text.strip():
                    raise HTTPException(status_code=400, detail="Could not extract text from policy file")
                
                # Compare using traditional method
                comparison_result = compare_with_policy(contract_text, policy_text)
        else:
            # Deterministic processor succeeded
            print(f"Using deterministic processor for policy comparison")
            policy_text = "DETERMINISTIC_PROCESSOR_USED - See result metadata"
            policy_metadata = {
                "source": "Deterministic Processor",
                "method": "FAISS_deterministic_retrieval",
                "processor_version": "1.0",
                "features": ["preprocessing", "stable_retrieval", "deterministic_llm", "verification", "caching"]
            }

        # Store in database
        comparison_doc = {
            "contract_filename": contract.filename,
            "policy_filename": policy_filename if policy_filename != "LEGAL_INDEX" else "Legal Index (FAISS)",
            "policy_id": policy_id,
            "contract_text": contract_text,
            "policy_text": policy_text,
            "policy_metadata": policy_metadata,
            "result": comparison_result,
            "type": "comparison",
            "legal_index_used": use_legal_index,
            "timestamp": datetime.now().isoformat()
        }
        
        doc_id = db['comparisons'].insert_one(comparison_doc).inserted_id

        return {
            "id": str(doc_id),
            "comparison": comparison_result,
            "contract_filename": contract.filename,
            "policy_filename": policy_filename if policy_filename != "LEGAL_INDEX" else "Legal Index (FAISS)",
            "legal_index_used": use_legal_index,
            "policy_metadata": policy_metadata
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing comparison: {str(e)}")
    
    finally:
        # Clean up temporary file
        if contract_path and os.path.exists(contract_path):
            os.unlink(contract_path)

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
