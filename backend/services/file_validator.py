"""
File validation utilities
"""
import os
import zipfile

def is_valid_pdf(filepath):
    """Check if a file is a valid PDF"""
    try:
        if not os.path.exists(filepath):
            return False, "File doesn't exist"
            
        if os.path.getsize(filepath) < 4:
            return False, "File is too small to be a valid PDF"
            
        # Check for PDF signature
        with open(filepath, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False, f"Not a PDF file (header: {header})"
            
        # Check for PDF signature
        with open(filepath, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False, "Missing PDF signature"
                
        return True, "Valid PDF file"
    except Exception as e:
        return False, f"Error validating PDF: {str(e)}"
        
def is_valid_docx(filepath):
    """Check if a file is a valid DOCX document"""
    try:
        if not os.path.exists(filepath):
            return False, "File doesn't exist"
            
        if os.path.getsize(filepath) < 10:
            return False, "File is too small to be a valid DOCX"
            
        # Check if it's a valid ZIP file (DOCX files are ZIP archives)
        if not zipfile.is_zipfile(filepath):
            return False, "Not a valid ZIP file (required for DOCX)"
            
        # Check for required files in the DOCX structure
        with zipfile.ZipFile(filepath) as docx:
            required_files = [
                'word/document.xml',
                '[Content_Types].xml',
                '_rels/.rels'
            ]
            
            # Check if at least one required file exists
            docx_files = docx.namelist()
            if not any(req_file in docx_files for req_file in required_files):
                return False, "Missing required DOCX structure files"
                
        return True, "Valid DOCX file"
    except zipfile.BadZipFile:
        return False, "Not a valid ZIP file (corrupted)"
    except Exception as e:
        return False, f"Error validating DOCX: {str(e)}"

def validate_file(filepath):
    """Validate a file based on its extension"""
    if not os.path.exists(filepath):
        return False, "File doesn't exist"
        
    _, ext = os.path.splitext(filepath.lower())
    
    if ext == '.pdf':
        return is_valid_pdf(filepath)
    elif ext == '.docx':
        return is_valid_docx(filepath)
    else:
        return False, f"Unsupported file format: {ext}"
