"""
Helper utilities for BeLagel
"""

import re
import hashlib
from typing import List, Optional
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text for consistent processing.
    
    Args:
        text: Input text
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)
    
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def calculate_similarity(score1: float, score2: float, method: str = "average") -> float:
    """
    Calculate similarity score between two values.
    
    Args:
        score1: First score
        score2: Second score
        method: Combination method (average, max, min)
    
    Returns:
        Combined similarity score
    """
    if method == "average":
        return (score1 + score2) / 2
    elif method == "max":
        return max(score1, score2)
    elif method == "min":
        return min(score1, score2)
    else:
        raise ValueError(f"Unknown method: {method}")


def generate_cache_key(query: str, metadata_filter: Optional[dict] = None) -> str:
    """
    Generate a unique cache key for a query.
    
    Args:
        query: User query
        metadata_filter: Optional metadata filter
    
    Returns:
        Cache key string
    """
    key_data = f"{query}:{metadata_filter}" if metadata_filter else query
    return hashlib.md5(key_data.encode("utf-8")).hexdigest()


def extract_article_number(text: str) -> Optional[str]:
    """
    Extract article number from text.
    
    Args:
        text: Text containing article reference
    
    Returns:
        Article number or None
    """
    # Match patterns like "125-modda", "125-m", "Modda 125"
    patterns = [
        r"(\d+)-modda",
        r"(\d+)-m",
        r"modda\s+(\d+)",
        r"(\d+)\s+modda",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
    
    Returns:
        List of sentences
    """
    # Simple sentence splitting for Uzbek
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]