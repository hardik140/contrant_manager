# backend/services/ocr_service.py

import io
import pytesseract
from pdf2image import convert_from_bytes
from docx import Document
from PIL import ImageOps, ImageFilter, Image
import pdfplumber
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from typing import Dict, List, Tuple, Any
import numpy as np
import math

def analyze_image_quality(img: Image.Image) -> Dict[str, float]:
    """
    Analyze image quality to determine if preprocessing is needed
    Returns metrics about contrast and noise
    """
    # Convert to grayscale for analysis
    if img.mode != 'L':
        img = ImageOps.grayscale(img)
    
    # Convert to numpy array for faster computation
    img_array = np.array(img)
    
    # Calculate histogram
    hist = np.histogram(img_array, bins=256, range=(0, 256))[0]
    hist = hist / hist.sum()  # Normalize
    
    # Calculate contrast (standard deviation)
    contrast = np.std(img_array)
    
    # Calculate noise (local variance)
    local_var = np.std(img_array[1:] - img_array[:-1])
    
    # Calculate edge sharpness
    edges_x = np.diff(img_array, axis=1)
    edges_y = np.diff(img_array, axis=0)
    edge_strength = np.mean(np.abs(edges_x)) + np.mean(np.abs(edges_y))
    
    return {
        "contrast": float(contrast),
        "noise": float(local_var),
        "edge_strength": float(edge_strength)
    }

def detect_page_layout(img: Image.Image) -> int:
    """
    Detect page layout and return appropriate PSM mode
    Returns: 4 for single column, 6 for multi-column
    """
    width, height = img.size
    gray = np.array(ImageOps.grayscale(img))
    
    # Divide image into vertical thirds
    third_width = width // 3
    densities = []
    
    # Calculate text density in each third
    for i in range(3):
        start = i * third_width
        end = start + third_width
        section = gray[:, start:end]
        density = np.mean(section < 128)  # Assuming dark text on light background
        densities.append(density)
    
    # If middle third has significantly less text, likely multi-column
    middle_density = densities[1]
    side_density = (densities[0] + densities[2]) / 2
    
    return 6 if middle_density < side_density * 0.7 else 4

def process_image_for_ocr(img: Image.Image) -> str:
    """Process a single image for OCR with optimizations"""
    # Analyze image quality
    quality_metrics = analyze_image_quality(img)
    needs_preprocessing = (
        quality_metrics["contrast"] < 50 or  # Low contrast
        quality_metrics["noise"] > 10 or     # High noise
        quality_metrics["edge_strength"] < 5  # Weak edges
    )
    
    if needs_preprocessing:
        # Apply preprocessing only if needed
        img = ImageOps.grayscale(img)
        img = img.filter(ImageFilter.SHARPEN)
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
    
    # Get original size
    orig_size = img.size
    
    # Try to crop margins if there are any
    bbox = img.getbbox()
    if bbox:
        # Only crop if we're not losing too much of the page
        crop_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        full_area = orig_size[0] * orig_size[1]
        if crop_area > 0.5 * full_area:  # Don't crop if we'd lose more than 50%
            img = img.crop(bbox)
    
    # Detect page layout and choose PSM mode
    psm_mode = detect_page_layout(img)
    
    # Perform OCR with dynamic PSM
    text = pytesseract.image_to_string(
        img,
        lang='eng',
        config=f'--oem 3 --psm {psm_mode}'
    )
    return text.strip()

def convert_pdf_chunk(args: Tuple[bytes, List[int]]) -> List[Image.Image]:
    """Convert a chunk of PDF pages to images"""
    pdf_bytes, page_numbers = args
    return convert_from_bytes(pdf_bytes, dpi=200, first_page=min(page_numbers)+1,
                            last_page=max(page_numbers)+1)

def process_page(args: Tuple[Image.Image, int]) -> Tuple[int, str, bool]:
    """Process a single page, returns (page_number, text, ocr_used)"""
    img, page_num = args
    try:
        text = process_image_for_ocr(img)
        return (page_num, text, True)
    except Exception as e:
        return (page_num, "", True)

def extract_text(file_bytes: bytes, file_type: str) -> Dict:
    """
    Extract text from DOCX or PDF using optimized parallel processing
    """
    if file_type == "application/pdf":
        return _extract_from_pdf(file_bytes)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def _extract_from_docx(file_bytes: bytes) -> Dict:
    """Extract text from DOCX file"""
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return {"text": text, "meta": {"source": "docx", "ocr_used": False, "pages": None}}
    except Exception as e:
        raise RuntimeError(f"DOCX extraction failed: {str(e)}")

def _extract_from_pdf(file_bytes: bytes) -> Dict:
    """Extract text from PDF using parallel processing for both conversion and OCR"""
    text_by_page: List[Tuple[int, str, bool]] = []
    ocr_used = False
    pages_count = 0

    try:
        # First try: extract text with pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_count = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_by_page.append((page_num, page_text.strip(), False))
                else:
                    text_by_page.append((page_num, "", True))

        # Collect pages needing OCR
        pages_needing_ocr = [(page_num, "") for page_num, text, needs_ocr in text_by_page if needs_ocr]
        
        if pages_needing_ocr:
            ocr_used = True
            
            # Split pages into chunks for parallel conversion
            cpu_count = max(1, multiprocessing.cpu_count() - 1)
            chunk_size = max(1, math.ceil(len(pages_needing_ocr) / cpu_count))
            page_chunks = [
                [p[0] for p in pages_needing_ocr[i:i + chunk_size]]
                for i in range(0, len(pages_needing_ocr), chunk_size)
            ]

            # Convert PDF chunks to images in parallel
            with ProcessPoolExecutor(max_workers=cpu_count) as executor:
                future_to_chunk = {
                    executor.submit(convert_pdf_chunk, (file_bytes, chunk)): chunk
                    for chunk in page_chunks
                }

                # Collect converted images and maintain page order
                pages_to_process = []
                for future in as_completed(future_to_chunk):
                    chunk_pages = future.result()
                    chunk_numbers = future_to_chunk[future]
                    pages_to_process.extend(zip(chunk_pages, chunk_numbers))

            # Process pages with OCR in parallel
            with ProcessPoolExecutor(max_workers=cpu_count) as executor:
                future_to_page = {
                    executor.submit(process_page, (img, page_num)): page_num
                    for img, page_num in pages_to_process
                }

                # Collect OCR results
                for future in as_completed(future_to_page):
                    page_num, text, _ = future.result()
                    # Update text for this page
                    for i, (orig_page_num, orig_text, needs_ocr) in enumerate(text_by_page):
                        if orig_page_num == page_num and needs_ocr:
                            text_by_page[i] = (page_num, text, True)
                            break

        # Combine all text in correct page order
        sorted_text = sorted(text_by_page, key=lambda x: x[0])
        combined_text = "\n".join(text for _, text, _ in sorted_text if text)

        return {
            "text": combined_text.strip(),
            "meta": {
                "source": "pdf",
                "ocr_used": ocr_used,
                "pages": pages_count
            }
        }

    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {str(e)}")