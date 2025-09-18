#!/usr/bin/env python3
"""
Legal Document Indexing System
Creates a FAISS-based semantic search index for legal documents (Indian Contract Act)

This script:
1. Loads a PDF document using PyMuPDF with pdfminer fallback
2. Extracts and cleans text content
3. Splits text into clauses/sections using sophisticated pattern matching
4. Generates embeddings using sentence-transformers
5. Stores vectors in FAISS index with cosine similarity
6. Saves metadata in JSONL format for efficient lookup
7. Provides semantic search functionality

Usage:
    python build_legal_index.py
    
Output:
    ./index/faiss.index - FAISS vector index
    ./index/ids.npy - Section ID mappings
    ./index/act_clauses.jsonl - Full text metadata
"""

import os
import re
import json
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LegalSection:
    """Represents a legal section/clause with metadata"""
    id: str
    title: str
    text: str
    section_type: str  # 'section', 'subsection', 'clause', 'provision'
    chapter: str = ""
    page_ref: str = ""

class LegalDocumentProcessor:
    """Processes legal documents and builds searchable indexes"""
    
    def __init__(self):
        self.sections = []
        self.model = None
        self.index = None
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF with pdfminer.six fallback
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        # Try PyMuPDF first (faster and better formatting)
        try:
            import fitz  # pymupdf
            doc = fitz.open(pdf_path)
            text_pages = []
            
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text("text")
                if page_text.strip():  # Only add non-empty pages
                    text_pages.append(f"[PAGE {page_num}]\n{page_text}")
            
            doc.close()
            full_text = "\n\n".join(text_pages)
            logger.info(f"Successfully extracted {len(full_text)} characters using PyMuPDF")
            return full_text
            
        except ImportError:
            logger.warning("PyMuPDF not available, trying pdfminer.six")
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}, trying pdfminer.six")
        
        # Fallback to pdfminer.six
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(pdf_path)
            logger.info(f"Successfully extracted {len(text)} characters using pdfminer.six")
            return text
        except ImportError:
            raise ImportError("Neither PyMuPDF nor pdfminer.six is available. Please install one of them.")
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        logger.info("Cleaning extracted text")
        
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces to single
        text = re.sub(r'\n ', '\n', text)        # Remove spaces after newlines
        
        # Fix common OCR/extraction issues
        text = text.replace('—', '-')  # Em dash to hyphen
        text = text.replace('"', '"').replace('"', '"')  # Smart quotes
        text = text.replace(''', "'").replace(''', "'")  # Smart apostrophes
        
        # Remove page headers/footers patterns
        text = re.sub(r'\[PAGE \d+\]', '', text)  # Remove page markers
        text = re.sub(r'^.*?(THE INDIAN CONTRACT ACT.*?)$', r'\1', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text.strip()

    def detect_section_patterns(self, text: str) -> List[LegalSection]:
        """
        Split text into legal sections using comprehensive pattern matching
        
        Detects patterns like:
        - "Section 2(a)" - Main sections with subsections
        - "29. Agreements void for uncertainty" - Numbered provisions
        - "CHAPTER II" - Chapter headers
        - "2A. Special provisions" - Amended sections
        
        Args:
            text: Cleaned text content
            
        Returns:
            List of LegalSection objects
        """
        logger.info("Detecting legal section patterns")
        
        sections = []
        lines = text.split('\n')
        current_section = None
        current_chapter = ""
        buffer = []
        
        # Enhanced regex patterns for different section types
        patterns = {
            'chapter': re.compile(r'^(CHAPTER\s+[IVXLCDM]+)\s*[-–]?\s*(.*?)$', re.IGNORECASE),
            'main_section': re.compile(r'^(Section\s+)?(\d+[A-Z]?)\s*[:\.-]\s*(.*?)$', re.IGNORECASE),
            'subsection': re.compile(r'^(\d+[A-Z]?)\s*\(([a-z]+)\)\s*[:\.-]?\s*(.*?)$', re.IGNORECASE),
            'numbered_provision': re.compile(r'^(\d+[A-Z]?)\s*\.\s*(.*?)$'),
            'lettered_clause': re.compile(r'^(\([a-z]+\))\s*(.*?)$'),
            'explanation': re.compile(r'^(Explanation\s*[:\.-]?\s*)(.*?)$', re.IGNORECASE),
            'illustration': re.compile(r'^(Illustration\s*[:\.-]?\s*)(.*?)$', re.IGNORECASE)
        }
        
        def save_current_section():
            """Save the current section buffer"""
            if current_section and buffer:
                text_content = ' '.join(buffer).strip()
                if text_content:  # Only save non-empty sections
                    sections.append(LegalSection(
                        id=current_section['id'],
                        title=current_section['title'],
                        text=text_content,
                        section_type=current_section['type'],
                        chapter=current_chapter
                    ))
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            matched = False
            
            # Check for chapter headers
            if match := patterns['chapter'].match(line):
                save_current_section()
                current_chapter = f"{match.group(1)} - {match.group(2)}"
                current_section = None
                buffer = []
                matched = True
                logger.debug(f"Found chapter: {current_chapter}")
            
            # Check for main sections (Section 2, Section 10A, etc.)
            elif match := patterns['main_section'].match(line):
                save_current_section()
                section_id = match.group(2)
                title = match.group(3)
                current_section = {
                    'id': f"Section_{section_id}",
                    'title': f"Section {section_id}: {title}",
                    'type': 'section'
                }
                buffer = [title] if title else []
                matched = True
                logger.debug(f"Found main section: {section_id}")
            
            # Check for subsections (2(a), 10(b), etc.)
            elif match := patterns['subsection'].match(line):
                save_current_section()
                section_id = match.group(1)
                subsection = match.group(2)
                title = match.group(3)
                current_section = {
                    'id': f"Section_{section_id}_{subsection}",
                    'title': f"Section {section_id}({subsection}): {title}",
                    'type': 'subsection'
                }
                buffer = [title] if title else []
                matched = True
                logger.debug(f"Found subsection: {section_id}({subsection})")
            
            # Check for numbered provisions (29. Agreements void...)
            elif match := patterns['numbered_provision'].match(line):
                save_current_section()
                provision_num = match.group(1)
                title = match.group(2)
                current_section = {
                    'id': f"Provision_{provision_num}",
                    'title': f"{provision_num}. {title}",
                    'type': 'provision'
                }
                buffer = [title] if title else []
                matched = True
                logger.debug(f"Found provision: {provision_num}")
            
            # Check for lettered clauses ((a), (b), etc.)
            elif match := patterns['lettered_clause'].match(line):
                save_current_section()
                clause_letter = match.group(1)
                content = match.group(2)
                current_section = {
                    'id': f"Clause_{clause_letter}",
                    'title': f"Clause {clause_letter}",
                    'type': 'clause'
                }
                buffer = [content] if content else []
                matched = True
                logger.debug(f"Found clause: {clause_letter}")
            
            # Check for explanations and illustrations
            elif match := patterns['explanation'].match(line):
                save_current_section()
                content = match.group(2)
                current_section = {
                    'id': f"Explanation_{line_num}",
                    'title': "Explanation",
                    'type': 'explanation'
                }
                buffer = [content] if content else []
                matched = True
            
            elif match := patterns['illustration'].match(line):
                save_current_section()
                content = match.group(2)
                current_section = {
                    'id': f"Illustration_{line_num}",
                    'title': "Illustration", 
                    'type': 'illustration'
                }
                buffer = [content] if content else []
                matched = True
            
            # If no pattern matched, add to current buffer
            if not matched and current_section:
                buffer.append(line)
            elif not matched and not current_section:
                # Handle text before first section
                if not sections or sections[-1].id != "Preamble":
                    sections.append(LegalSection(
                        id="Preamble",
                        title="Preamble and Introduction",
                        text=line,
                        section_type="preamble",
                        chapter=current_chapter
                    ))
                else:
                    # Append to existing preamble
                    sections[-1].text += " " + line
        
        # Save the last section
        save_current_section()
        
        logger.info(f"Detected {len(sections)} legal sections")
        return sections

    def build_embeddings_index(self, sections: List[LegalSection], output_dir: str = "./index") -> Tuple[Any, Any]:
        """
        Generate embeddings and build FAISS index
        
        Args:
            sections: List of legal sections
            output_dir: Directory to save index files
            
        Returns:
            Tuple of (faiss_index, sentence_transformer_model)
        """
        logger.info("Building embeddings and FAISS index")
        
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
        except ImportError as e:
            raise ImportError(f"Required packages not installed: {e}")
        
        # Use a high-quality model for legal text
        model_name = "sentence-transformers/all-mpnet-base-v2"
        logger.info(f"Loading model: {model_name}")
        model = SentenceTransformer(model_name)
        
        # Prepare texts for embedding (combine title and content for better context)
        texts_to_embed = []
        for section in sections:
            # Combine title and text for richer embeddings
            combined_text = f"{section.title}. {section.text}"
            texts_to_embed.append(combined_text)
        
        logger.info(f"Generating embeddings for {len(texts_to_embed)} sections")
        
        # Generate embeddings with normalization for cosine similarity
        embeddings = model.encode(
            texts_to_embed,
            convert_to_numpy=True,
            normalize_embeddings=True,  # Normalize for cosine similarity
            show_progress_bar=True,
            batch_size=32
        )
        
        # Build FAISS index (IndexFlatIP for cosine similarity with normalized vectors)
        dimension = embeddings.shape[1]
        logger.info(f"Building FAISS index with dimension {dimension}")
        
        index = faiss.IndexFlatIP(dimension)  # Inner product = cosine similarity for normalized vectors
        index.add(embeddings.astype(np.float32))
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = os.path.join(output_dir, "faiss.index")
        faiss.write_index(index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save section IDs for lookup
        ids_array = np.array([section.id for section in sections])
        ids_path = os.path.join(output_dir, "ids.npy")
        np.save(ids_path, ids_array)
        logger.info(f"Saved section IDs to {ids_path}")
        
        # Save full metadata as JSONL
        jsonl_path = os.path.join(output_dir, "act_clauses.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for section in sections:
                section_dict = {
                    "id": section.id,
                    "title": section.title,
                    "text": section.text,
                    "section_type": section.section_type,
                    "chapter": section.chapter,
                    "page_ref": section.page_ref
                }
                f.write(json.dumps(section_dict, ensure_ascii=False) + "\n")
        logger.info(f"Saved metadata to {jsonl_path}")
        
        self.model = model
        self.index = index
        self.sections = sections
        
        return index, model

class LegalSearchEngine:
    """Semantic search engine for legal documents"""
    
    def __init__(self, index_dir: str = "./index"):
        """
        Initialize search engine with pre-built index
        
        Args:
            index_dir: Directory containing index files
        """
        self.index_dir = index_dir
        self.index = None
        self.model = None
        self.sections = []
        self.section_ids = None
        
    def load_index(self):
        """Load pre-built FAISS index and metadata"""
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(f"Required packages not installed: {e}")
        
        logger.info(f"Loading search index from {self.index_dir}")
        
        # Load FAISS index
        index_path = os.path.join(self.index_dir, "faiss.index")
        self.index = faiss.read_index(index_path)
        
        # Load model
        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        
        # Load section IDs
        ids_path = os.path.join(self.index_dir, "ids.npy")
        self.section_ids = np.load(ids_path, allow_pickle=True)
        
        # Load section metadata
        jsonl_path = os.path.join(self.index_dir, "act_clauses.jsonl")
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                section_data = json.loads(line.strip())
                self.sections.append(LegalSection(**section_data))
        
        logger.info(f"Loaded index with {len(self.sections)} sections")

    def search(self, query: str, top_k: int = 5, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform semantic search over legal sections
        
        Args:
            query: Search query
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of search results with scores and metadata
        """
        if not self.index or not self.model:
            raise ValueError("Search index not loaded. Call load_index() first.")
        
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        
        # Generate query embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(np.float32)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= min_score:  # Filter by minimum score
                section_id = self.section_ids[idx]
                
                # Find corresponding section metadata
                section = next((s for s in self.sections if s.id == section_id), None)
                
                if section:
                    results.append({
                        "id": section.id,
                        "title": section.title,
                        "text": section.text,
                        "section_type": section.section_type,
                        "chapter": section.chapter,
                        "similarity_score": float(score),
                        "rank": len(results) + 1
                    })
        
        logger.info(f"Found {len(results)} relevant sections")
        return results

def main():
    """Main execution function"""
    # Configuration
    PDF_PATH = "./policies/A187209.pdf"  # Updated path based on your structure
    INDEX_DIR = "./index"
    
    # Check if PDF exists
    if not os.path.exists(PDF_PATH):
        # Try alternative paths
        alt_paths = [
            "./A187209.pdf",
            "./backend/policies/A187209.pdf",
            "../A187209.pdf"
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                PDF_PATH = alt_path
                break
        else:
            logger.error(f"PDF file not found at {PDF_PATH} or alternative locations")
            return
    
    logger.info(f"Using PDF: {PDF_PATH}")
    
    # Step 1: Initialize processor and extract text
    processor = LegalDocumentProcessor()
    raw_text = processor.extract_text_from_pdf(PDF_PATH)
    
    # Step 2: Clean and process text
    clean_text = processor.clean_text(raw_text)
    
    # Step 3: Split into sections
    sections = processor.detect_section_patterns(clean_text)
    
    # Step 4: Build embeddings and FAISS index
    index, model = processor.build_embeddings_index(sections, INDEX_DIR)
    
    # Step 5: Demo the search functionality
    logger.info("="*50)
    logger.info("SEARCH ENGINE DEMO")
    logger.info("="*50)
    
    search_engine = LegalSearchEngine(INDEX_DIR)
    search_engine.load_index()
    
    # Example queries
    test_queries = [
        "Agreements void for uncertainty",
        "consideration for agreement", 
        "contract formation",
        "breach of contract remedies",
        "void and voidable contracts"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")
        results = search_engine.search(query, top_k=3, min_score=0.3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} (Score: {result['similarity_score']:.3f})")
            print(f"   Type: {result['section_type']} | Chapter: {result['chapter']}")
            print(f"   Text: {result['text'][:200]}...")

if __name__ == "__main__":
    main()
