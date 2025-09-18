"""
Text Normalization Service

This module provides text preprocessing and normalization functionality
for contract analysis to improve consistency and accuracy.
"""

import re
import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class NormalizationStats:
    """Statistics about text normalization operations"""
    original_length: int
    normalized_length: int
    characters_cleaned: int
    dates_standardized: int
    currencies_normalized: int
    whitespace_normalized: int
    parties_masked: int

class TextNormalizer:
    """Text normalization for contract analysis"""
    
    def __init__(self):
        # Common party placeholders
        self.party_patterns = [
            r'\b(?:Company|Corporation|Corp\.?|Inc\.?|LLC|Ltd\.?)\b',
            r'\b(?:Client|Customer|Vendor|Supplier|Contractor)\b',
            r'\b(?:Lessor|Lessee|Landlord|Tenant)\b'
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b'
        ]
        
        # Currency patterns
        self.currency_patterns = [
            r'\$[\d,]+\.?\d*',  # $1,000.00
            r'USD?\s*[\d,]+\.?\d*',  # USD 1000
            r'[\d,]+\.?\d*\s*(?:dollars?|USD)',  # 1000 dollars
            r'₹[\d,]+\.?\d*',  # ₹1,000
            r'INR\s*[\d,]+\.?\d*'  # INR 1000
        ]
    
    def normalize_text(self, text: str, mask_parties: bool = False, 
                      standardize_dates: bool = True, 
                      normalize_currencies: bool = True) -> Tuple[str, NormalizationStats]:
        """
        Normalize contract text for better analysis
        
        Args:
            text: Raw contract text
            mask_parties: Whether to mask party names with placeholders
            standardize_dates: Whether to standardize date formats
            normalize_currencies: Whether to normalize currency formats
            
        Returns:
            Tuple of (normalized_text, normalization_stats)
        """
        if not text or not isinstance(text, str):
            return "", NormalizationStats(0, 0, 0, 0, 0, 0, 0)
        
        original_length = len(text)
        normalized_text = text
        stats = NormalizationStats(
            original_length=original_length,
            normalized_length=0,
            characters_cleaned=0,
            dates_standardized=0,
            currencies_normalized=0,
            whitespace_normalized=0,
            parties_masked=0
        )
        
        # Step 1: Normalize whitespace - preserve newlines but normalize other whitespace
        original_ws_len = len(normalized_text)
        # Replace multiple spaces/tabs with single space, but preserve newlines
        normalized_text = re.sub(r'[ \t]+', ' ', normalized_text)  # Multiple spaces/tabs to single space
        normalized_text = re.sub(r'\n\s*\n+', '\n\n', normalized_text)  # Multiple newlines to double
        normalized_text = normalized_text.strip()
        stats.whitespace_normalized = original_ws_len - len(normalized_text)
        
        # Step 2: Remove/normalize common artifacts
        artifacts_removed = 0
        
        # Remove page numbers
        page_pattern = r'\b[Pp]age\s+\d+\s+(?:of|/)\s+\d+\b'
        artifacts_removed += len(re.findall(page_pattern, normalized_text))
        normalized_text = re.sub(page_pattern, '', normalized_text)
        
        # Remove header/footer patterns
        header_pattern = r'^.*?(?:CONFIDENTIAL|PROPRIETARY|DRAFT).*?$'
        header_matches = re.findall(header_pattern, normalized_text, re.MULTILINE)
        artifacts_removed += len(header_matches)
        normalized_text = re.sub(header_pattern, '', normalized_text, flags=re.MULTILINE)
        
        stats.characters_cleaned = artifacts_removed
        
        # Step 3: Standardize dates
        if standardize_dates:
            for pattern in self.date_patterns:
                matches = re.findall(pattern, normalized_text, re.IGNORECASE)
                stats.dates_standardized += len(matches)
                # Replace with standardized format [DATE]
                normalized_text = re.sub(pattern, '[DATE]', normalized_text, flags=re.IGNORECASE)
        
        # Step 4: Normalize currencies
        if normalize_currencies:
            for pattern in self.currency_patterns:
                matches = re.findall(pattern, normalized_text, re.IGNORECASE)
                stats.currencies_normalized += len(matches)
                # Replace with standardized format [AMOUNT]
                normalized_text = re.sub(pattern, '[AMOUNT]', normalized_text, flags=re.IGNORECASE)
        
        # Step 5: Mask parties (optional)
        if mask_parties:
            for pattern in self.party_patterns:
                matches = re.findall(pattern, normalized_text, re.IGNORECASE)
                stats.parties_masked += len(matches)
                normalized_text = re.sub(pattern, '[PARTY]', normalized_text, flags=re.IGNORECASE)
        
        # Step 6: Final cleanup - preserve newlines
        normalized_text = re.sub(r'[ \t]+', ' ', normalized_text)  # Only normalize spaces/tabs, preserve newlines
        normalized_text = normalized_text.strip()
        
        # Ensure we don't return empty text unless input was empty
        if not normalized_text and text.strip():
            normalized_text = text.strip()
        
        stats.normalized_length = len(normalized_text)
        
        return normalized_text, stats
    
    def extract_key_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract key entities from contract text
        
        Returns:
            Dictionary with lists of dates, amounts, parties, etc.
        """
        entities = {
            "dates": [],
            "amounts": [],
            "parties": [],
            "sections": []
        }
        
        # Extract dates
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["dates"].extend(matches)
        
        # Extract amounts
        for pattern in self.currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["amounts"].extend(matches)
        
        # Extract section references
        section_pattern = r'(?:Section|Article|Clause)\s+(\d+(?:\.\d+)*)'
        entities["sections"] = re.findall(section_pattern, text, re.IGNORECASE)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities

# Global instance
text_normalizer = TextNormalizer()

def normalize_contract_text(text: str, **kwargs) -> Tuple[str, NormalizationStats]:
    """Convenience function for text normalization"""
    return text_normalizer.normalize_text(text, **kwargs)

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Convenience function for entity extraction"""
    return text_normalizer.extract_key_entities(text)