import docx2txt
import fitz  # PyMuPDF
import os
import io
import logging
from services.ocr_service import extract_text as ocr_extract_text
from services.text_normalizer import normalize_contract_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """Extract text from PDF file using PyMuPDF"""
    text = ""
    try:
        # Validate file before opening
        if not os.path.exists(file_path):
            raise ValueError(f"PDF file not found at {file_path}")
            
        if not os.path.getsize(file_path) > 0:
            raise ValueError("PDF file is empty")
        
        # Check for PDF signature
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise ValueError(f"Not a valid PDF file (header: {header})")
            
        # Open and extract text
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"PDF extraction error for {file_path}: {str(e)}")
        raise ValueError(f"Error extracting text from PDF: {str(e)}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file using docx2txt"""
    try:
        # Validate file before processing
        if not os.path.exists(file_path):
            raise ValueError(f"DOCX file not found at {file_path}")
            
        if not os.path.getsize(file_path) > 0:
            raise ValueError("DOCX file is empty")
            
        # Basic validation to check if it's a ZIP file (DOCX files are ZIP archives)
        import zipfile
        if not zipfile.is_zipfile(file_path):
            raise ValueError("File is not a valid DOCX document (not a zip file)")
            
        # Extract text
        text = docx2txt.process(file_path)
        if text is None:
            return ""
        return text
    except zipfile.BadZipFile:
        print(f"Bad zip file: {file_path}")
        raise ValueError("File is not a valid DOCX document (bad zip file)")
    except Exception as e:
        print(f"DOCX extraction error for {file_path}: {str(e)}")
        raise ValueError(f"Error extracting text from DOCX: {str(e)}")

def extract_text_with_ocr(file_path):
    """Extract text using advanced OCR processing"""
    try:
        # Read file as bytes
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
            
        # Determine file type
        _, file_ext = os.path.splitext(file_path.lower())
        if file_ext == '.pdf':
            file_type = "application/pdf"
        elif file_ext == '.docx':
            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            raise ValueError(f"Unsupported file format for OCR: {file_ext}")
        
        # Use OCR service
        result = ocr_extract_text(file_bytes, file_type)
        return result["text"]
    except Exception as e:
        print(f"OCR extraction failed: {str(e)}")
        raise ValueError(f"Failed to extract text with OCR: {str(e)}")

def extract_text(file_path):
    """Extract text from file based on extension"""
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    # More robust extension extraction
    _, file_ext = os.path.splitext(file_path.lower())
    
    # Log the file path and extension for debugging
    logger.info(f"Extracting text from file: {file_path}, extension: {file_ext}")
    
    extraction_metadata = {
        "extraction_method": "unknown",
        "ocr_used": False,
        "file_size": os.path.getsize(file_path),
        "file_ext": file_ext
    }
    
    try:
        # Try standard extraction first
        if file_ext == ".pdf":
            text = extract_text_from_pdf(file_path)
            extraction_metadata["extraction_method"] = "pdf_direct"
        elif file_ext == ".docx":
            text = extract_text_from_docx(file_path)
            extraction_metadata["extraction_method"] = "docx_direct"
        else:
            raise ValueError(f"Unsupported file format: {file_ext} for file: {file_path}")
            
        # If we got text, normalize and return it
        if text and text.strip():
            logger.info(f"Standard extraction successful, text length: {len(text)}")
            
            # Apply text normalization
            try:
                normalized_text, norm_stats = normalize_contract_text(text)
                logger.info(f"Text normalized: {norm_stats.characters_cleaned} chars cleaned, "
                           f"{norm_stats.dates_standardized} dates standardized")
                return normalized_text, extraction_metadata
            except Exception as e:
                logger.warning(f"Text normalization failed: {str(e)}, returning raw text")
                return text, extraction_metadata
            
        # If standard extraction didn't yield text, try OCR
        logger.info(f"Standard extraction produced no text, trying OCR for: {file_path}")
        ocr_result = extract_text_with_ocr(file_path)
        extraction_metadata["extraction_method"] = "ocr"
        extraction_metadata["ocr_used"] = True
        
        # Normalize OCR text
        try:
            normalized_text, norm_stats = normalize_contract_text(ocr_result)
            logger.info(f"OCR text normalized: {norm_stats.characters_cleaned} chars cleaned")
            return normalized_text, extraction_metadata
        except Exception as e:
            logger.warning(f"OCR text normalization failed: {str(e)}")
            return ocr_result, extraction_metadata
    
    except Exception as e:
        # Fall back to OCR if standard extraction fails
        logger.warning(f"Standard extraction failed: {str(e)}, trying OCR for: {file_path}")
        try:
            ocr_result = extract_text_with_ocr(file_path)
            extraction_metadata["extraction_method"] = "ocr_fallback"
            extraction_metadata["ocr_used"] = True
            extraction_metadata["error_message"] = str(e)
            
            # Normalize OCR fallback text
            try:
                normalized_text, norm_stats = normalize_contract_text(ocr_result)
                return normalized_text, extraction_metadata
            except Exception as norm_e:
                logger.warning(f"OCR fallback text normalization failed: {str(norm_e)}")
                return ocr_result, extraction_metadata
                
        except Exception as ocr_e:
            logger.error(f"Both standard and OCR extraction failed: {str(ocr_e)}")
            extraction_metadata["error_message"] = f"Standard: {str(e)}, OCR: {str(ocr_e)}"
            raise ValueError(f"Failed to extract text: {str(ocr_e)}")

# Backward compatibility function
def extract_text_legacy(file_path):
    """Legacy function for backward compatibility"""
    result, metadata = extract_text(file_path)
    return result
