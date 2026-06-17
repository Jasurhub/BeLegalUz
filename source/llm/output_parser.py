"""
Parser for LLM output extraction
"""

import json
import re
from typing import List, Dict, Optional, Any
from source.utils.logger import get_logger

logger = get_logger(__name__)


class OutputParser:
    """
    Parses and extracts structured data from LLM responses.
    """
    
    def __init__(self):
        """Initialize parser"""
        self.logger = logger
    
    def extract_citations(self, text: str) -> List[Dict[str, str]]:
        """
        Extract legal citations from text.
        
        Args:
            text: LLM response text
        
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        # Pattern 1: "Mehnat kodeksining 100-moddasi"
        pattern1 = re.compile(
            r"([A-Za-z\s']+)\s+kodeks(?:ining)?\s+(\d+)-modda",
            re.IGNORECASE
        )
        
        # Pattern 2: "MK 100-modda"
        pattern2 = re.compile(
            r"(MK|JK|FK|SK|MJK|OK|JPK|FPK|IPK)\s+(\d+)-modda",
            re.IGNORECASE
        )
        
        # Pattern 3: "Modda 100"
        pattern3 = re.compile(
            r"modda\s+(\d+)",
            re.IGNORECASE
        )
        
        # Extract from patterns
        for match in pattern1.finditer(text):
            code_name = match.group(1).strip()
            article_number = match.group(2)
            citations.append({
                "code_name": code_name,
                "article_number": article_number
            })
        
        for match in pattern2.finditer(text):
            short_code = match.group(1).upper()
            article_number = match.group(2)
            citations.append({
                "code_short": short_code,
                "article_number": article_number
            })
        
        # Remove duplicates
        unique_citations = []
        seen = set()
        for citation in citations:
            key = (
                citation.get("code_name", citation.get("code_short")),
                citation["article_number"]
            )
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        return unique_citations
    
    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text.
        
        Args:
            text: Text containing JSON
        
        Returns:
            Parsed JSON or None
        """
        # Try to find JSON in text
        json_pattern = re.compile(r'\{[^{}]*\}|\{[^{}]*(\{[^{}]*\}[^{}]*)*\}')
        
        matches = json_pattern.findall(text)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    def clean_response(self, text: str) -> str:
        """
        Clean LLM response text.
        
        Args:
            text: Raw response text
        
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common prefixes
        prefixes = ["Javob:", "Answer:", "Response:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text.strip()