import docx2txt
import fitz  # PyMuPDF
import os

def extract_text_from_pdf(file_path):
    """Extract text from PDF file using PyMuPDF"""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file using docx2txt"""
    try:
        text = docx2txt.process(file_path)
        if text is None:
            return ""
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from DOCX: {str(e)}")

def extract_text(file_path):
    """Extract text from file based on extension"""
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    file_ext = file_path.lower()
    if file_ext.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_ext.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")
