"""
API routes for clause analysis functionality with legal index integration
"""

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from services.clause_analyzer import analyze_clause, detect_clauses
from services.enhanced_clause_analyzer import detect_clauses_enhanced, analyze_clause_enhanced
from typing import Dict, Any, Optional, List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ClauseAnalysisRequest(BaseModel):
    reference_clause: str
    user_clause: str

class AnalysisProvenance(BaseModel):
    method: str
    similarity_score: Optional[float] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    fallback_used: bool = False
    error_occurred: bool = False
    error_message: Optional[str] = None

class ClauseAnalysisResponse(BaseModel):
    status: str
    explanation: str
    suggestion: str
    provenance: AnalysisProvenance

class ContractTextRequest(BaseModel):
    text: str

class ClauseDetectionResponse(BaseModel):
    id: int
    title: str
    text: str
    provenance: AnalysisProvenance
    extraction_method: str = "enhanced"
    ocr_used: bool = False
    legal_context: Optional[List[Dict[str, Any]]] = []
    legal_relevance_score: Optional[float] = 0.0
    enhanced_title: Optional[str] = None

@router.post("/analyze-clause/", response_model=ClauseAnalysisResponse)
async def analyze_clause_endpoint(request: ClauseAnalysisRequest):
    """
    Analyze a user clause against a reference clause using enhanced legal index
    
    Args:
        request: Contains reference_clause and user_clause
        
    Returns:
        Analysis result with legal context and compliance information
    """
    try:
        logger.info(f"Analyzing clause with enhanced legal context")
        logger.info(f"Reference clause length: {len(request.reference_clause)}")
        logger.info(f"User clause length: {len(request.user_clause)}")
        
        # Use enhanced analyzer that incorporates legal index
        result = analyze_clause_enhanced(
            reference_clause=request.reference_clause,
            user_clause=request.user_clause
        )
        
        # Convert provenance dict to model
        provenance_data = result.pop("provenance", {})
        provenance = AnalysisProvenance(**provenance_data)
        
        response = ClauseAnalysisResponse(
            status=result["status"],
            explanation=result["explanation"], 
            suggestion=result["suggestion"],
            provenance=provenance
        )
        
        logger.info(f"Enhanced clause analysis completed: {result['status']}")
        return response
        
    except Exception as e:
        logger.error(f"Error in enhanced analyze_clause_endpoint: {str(e)}")
        # Fallback to standard analysis
        try:
            logger.info("Falling back to standard clause analysis")
            result = analyze_clause(request.reference_clause, request.user_clause)
            
            provenance_data = result.pop("provenance", {})
            provenance = AnalysisProvenance(**provenance_data)
            
            return ClauseAnalysisResponse(
                status=result["status"],
                explanation=result["explanation"], 
                suggestion=result["suggestion"],
                provenance=provenance
            )
        except Exception as fallback_error:
            logger.error(f"Fallback analysis also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing clause: {str(e)}"
            )

@router.post("/batch-analyze-clauses/")
async def batch_analyze_clauses(
    clauses: Dict[str, Dict[str, str]] = Body(...)
):
    """
    Batch analyze multiple clauses
    
    Expected input format:
    {
        "clause_id1": {
            "reference_clause": "...",
            "user_clause": "..."
        },
        "clause_id2": {
            "reference_clause": "...",
            "user_clause": "..."
        },
        ...
    }
    
    Returns results in the same structure with analysis results
    """
    results = {}
    
    logger.info(f"Batch analyzing {len(clauses)} clause pairs")
    
    for clause_id, clause_data in clauses.items():
        reference = clause_data.get("reference_clause", "")
        user = clause_data.get("user_clause", "")
        
        try:
            # Use enhanced analyzer for better legal context
            analysis = analyze_clause_enhanced(reference, user)
            # Convert provenance dict to ensure serialization
            provenance_data = analysis.pop("provenance", {})
            analysis["provenance"] = AnalysisProvenance(**provenance_data)
            results[clause_id] = analysis
        except Exception as e:
            logger.error(f"Error analyzing clause {clause_id}: {str(e)}")
            results[clause_id] = {
                "status": "error",
                "explanation": f"Error analyzing clause: {str(e)}",
                "suggestion": "Please check input format and try again.",
                "provenance": AnalysisProvenance(
                    method="error",
                    error_occurred=True,
                    error_message=str(e)
                )
            }
    
    return {"results": results}

@router.post("/detect-clauses/", response_model=List[ClauseDetectionResponse])
async def detect_clauses_endpoint(request: ContractTextRequest):
    """
    Enhanced clause detection using legal index for better accuracy
    
    Args:
        request: The contract text to analyze
        
    Returns:
        List of detected clauses with legal context and enhanced metadata
    """
    try:
        logger.info(f"Starting enhanced clause detection for text of length: {len(request.text)}")
        
        # Use enhanced detection that incorporates legal index
        result = detect_clauses_enhanced(request.text)
        
        # Convert provenance dicts to models for each clause
        enhanced_result = []
        for clause in result:
            # Ensure all required fields are present
            clause.setdefault('legal_context', [])
            clause.setdefault('legal_relevance_score', 0.0)
            clause.setdefault('enhanced_title', None)
            clause.setdefault('extraction_method', 'enhanced')
            clause.setdefault('ocr_used', False)
            
            # Convert provenance dict to model
            provenance_data = clause.pop("provenance", {})
            
            # Create the response object
            clause_response = ClauseDetectionResponse(
                id=clause.get('id', 0),
                title=clause.get('title', 'Untitled Clause'),
                text=clause.get('text', ''),
                provenance=AnalysisProvenance(**provenance_data),
                extraction_method=clause.get('extraction_method', 'enhanced'),
                ocr_used=clause.get('ocr_used', False),
                legal_context=clause.get('legal_context', []),
                legal_relevance_score=clause.get('legal_relevance_score', 0.0),
                enhanced_title=clause.get('enhanced_title', None)
            )
            enhanced_result.append(clause_response)
        
        logger.info(f"Enhanced clause detection completed: {len(enhanced_result)} clauses found")
        logger.info(f"Clauses with legal context: {sum(1 for c in enhanced_result if c.legal_context)}")
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Error in enhanced detect_clauses_endpoint: {str(e)}")
        # Fallback to standard detection
        try:
            logger.info("Falling back to standard clause detection")
            result = detect_clauses(request.text)
            
            # Convert to enhanced format
            fallback_result = []
            for clause in result:
                clause.setdefault('legal_context', [])
                clause.setdefault('legal_relevance_score', 0.0)
                clause.setdefault('enhanced_title', None)
                clause.setdefault('extraction_method', 'standard_fallback')
                
                # Convert provenance dict to model
                provenance_data = clause.pop("provenance", {})
                
                # Create the response object
                clause_response = ClauseDetectionResponse(
                    id=clause.get('id', 0),
                    title=clause.get('title', 'Untitled Clause'),
                    text=clause.get('text', ''),
                    provenance=AnalysisProvenance(**provenance_data),
                    extraction_method=clause.get('extraction_method', 'standard_fallback'),
                    ocr_used=clause.get('ocr_used', False),
                    legal_context=clause.get('legal_context', []),
                    legal_relevance_score=clause.get('legal_relevance_score', 0.0),
                    enhanced_title=clause.get('enhanced_title', None)
                )
                fallback_result.append(clause_response)
            
            logger.info(f"Standard fallback detection completed: {len(fallback_result)} clauses")
            return fallback_result
            
        except Exception as fallback_error:
            logger.error(f"Fallback detection also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error detecting clauses: {str(e)}"
            )
