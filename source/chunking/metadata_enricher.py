"""
Metadata enrichment for chunks
"""

from datetime import datetime
from typing import Dict, Any, Optional
from source.utils.logger import get_logger

logger = get_logger(__name__)


class MetadataEnricher:
    """
    Enriches chunks with additional metadata for better filtering and retrieval.
    """
    
    def __init__(self):
        """Initialize metadata enricher"""
        self.logger = logger
    
    def enrich(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich chunk with additional metadata.
        
        Args:
            chunk: Original chunk dictionary
        
        Returns:
            Enriched chunk dictionary
        """
        enriched = chunk.copy()
        
        # Add timestamp
        enriched["metadata"]["indexed_at"] = datetime.utcnow().isoformat()
        
        # Add content statistics
        content = chunk.get("content", "")
        enriched["metadata"]["content_length"] = len(content)
        enriched["metadata"]["word_count"] = len(content.split())
        
        # Add version tracking
        enriched["metadata"]["version"] = "1.0"
        
        # Add source type
        enriched["metadata"]["source_type"] = "legal_code"
        
        # Validate and clean metadata
        enriched["metadata"] = self._clean_metadata(enriched["metadata"])
        
        return enriched
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate metadata.
        
        Args:
            metadata: Original metadata
        
        Returns:
            Cleaned metadata
        """
        cleaned = {}
        
        for key, value in metadata.items():
            # Skip None values
            if value is None:
                continue
            
            # Convert non-serializable types
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, (list, dict)):
                # Keep simple lists and dicts
                try:
                    import json
                    json.dumps(value)  # Test if serializable
                    cleaned[key] = value
                except (TypeError, ValueError):
                    self.logger.warning(f"Skipping non-serializable metadata: {key}")
            else:
                cleaned[key] = str(value)
        
        return cleaned
    
    def batch_enrich(
        self, 
        chunks: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Enrich multiple chunks.
        
        Args:
            chunks: List of chunks
        
        Returns:
            List of enriched chunks
        """
        self.logger.info(f"Enriching metadata for {len(chunks)} chunks")
        return [self.enrich(chunk) for chunk in chunks]