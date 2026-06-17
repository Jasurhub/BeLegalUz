"""
Vector store implementation using Qdrant
"""

from typing import List, Optional, Tuple, Dict, Any, Union
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    SearchParams
)
from source.utils.logger import get_logger
from source.utils.config import get_config
from .schema import ChunkPayload
from .collection_manager import CollectionManager

logger = get_logger(__name__)


class VectorStore:
    """
    Vector store for legal document embeddings using Qdrant.
    """

    def __init__(self):
        """Initialize vector store"""
        self.config = get_config()
        self.logger = logger

        # Initialize Qdrant client
        qdrant_url = self.config.vectordb.get("url", "http://localhost:6333")
        qdrant_api_key = self.config.vectordb.get("api_key")

        self.client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            prefer_grpc=True
        )

        self.collection_manager = CollectionManager(self.client)
        self.collection_name = self.config.vectordb.get(
            "collection_name", "uzbek_legal_codes"
        )

        self.logger.info(f"Vector store initialized: {qdrant_url}")

    def initialize(self, recreate: bool = False) -> bool:
        """
        Initialize vector store and collection.

        Args:
            recreate: Whether to recreate collection

        Returns:
            True if successful
        """
        return self.collection_manager.create_collection(recreate=recreate)

    async def upsert(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upsert chunks with embeddings into vector store.

        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors

        Returns:
            True if successful
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")

        points = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Generate point ID
            point_id = chunk.get("id", f"point_{i}")

            # Create payload
            payload = ChunkPayload(
                code_name=chunk["metadata"]["code_name"],
                code_short=chunk["metadata"]["code_short"],
                article_number=chunk["metadata"]["article_number"],
                content=chunk["content"],
                chapter=chunk["metadata"].get("chapter"),
                part_number=chunk["metadata"].get("part_number"),
                chunk_type=chunk["metadata"].get("chunk_type", "article"),
                chunk_number=chunk["metadata"].get("chunk_number"),
                is_active=chunk["metadata"].get("is_active", True),
                effective_date=chunk["metadata"].get("effective_date"),
                indexed_at=chunk["metadata"].get("indexed_at"),
                content_length=chunk["metadata"].get("content_length"),
                word_count=chunk["metadata"].get("word_count"),
                version=chunk["metadata"].get("version", "1.0"),
                source_type=chunk["metadata"].get("source_type", "legal_code")
            )

            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload.to_dict()
            )
            points.append(point)

        try:
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
                self.logger.debug(f"Upserted batch {i//batch_size + 1}")

            self.logger.info(f"Upserted {len(points)} points to vector store")
            return True

        except Exception as e:
            self.logger.error(f"Error upserting to vector store: {e}")
            return False

    async def search(
            self,
            query_embedding: List[float],
            top_k: int = 5,
            metadata_filter: Optional[Dict[str, Any]] = None,
            score_threshold: float = 0.0
    ) -> List[Tuple[ChunkPayload, float]]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            metadata_filter: Metadata filter dictionary
            score_threshold: Minimum similarity score

        Returns:
            List of (payload, score) tuples
        """
        try:
            # Build filter
            qdrant_filter = None
            if metadata_filter:
                qdrant_filter = self._build_filter(metadata_filter)

            # Search - YANGILANGAN!
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=top_k,
                score_threshold=score_threshold if score_threshold > 0 else None,
                search_params=SearchParams(
                    hnsw_ef=128,
                    exact=False
                ),
                with_payload=["code_name", "code_short", "article_number",
                              "content", "chapter", "is_active"]
                # with_vector=False olib tashlandi!
            )

            # Convert results
            search_results = []
            for result in results:
                payload = ChunkPayload.from_dict(result.payload)
                search_results.append((payload, result.score))

            self.logger.debug(f"Search returned {len(search_results)} results")
            return search_results

        except Exception as e:
            self.logger.error(f"Error searching vector store: {e}")
            return []

    def _build_filter(self, metadata_filter: Dict[str, Any]) -> Filter:
        """
        Build Qdrant filter from metadata dictionary.

        Args:
            metadata_filter: Metadata filter

        Returns:
            Qdrant Filter object
        """
        conditions = []

        for key, value in metadata_filter.items():
            if value is None:
                continue

            if isinstance(value, bool):
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            elif isinstance(value, str):
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            elif isinstance(value, (int, float)):
                conditions.append(
                    FieldCondition(
                        key=key,
                        range=Range(gte=value, lte=value)
                    )
                )

        return Filter(must=conditions) if conditions else None

    async def delete_by_filter(self, metadata_filter: Dict[str, Any]) -> int:
        """
        Delete points matching filter.

        Args:
            metadata_filter: Metadata filter

        Returns:
            Number of deleted points
        """
        try:
            qdrant_filter = self._build_filter(metadata_filter)

            if qdrant_filter:
                response = self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=qdrant_filter
                )
                self.logger.info(f"Deleted points matching filter")
                return 1
            return 0
            
        except Exception as e:
            self.logger.error(f"Error deleting points: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.collection_manager.get_stats()
    
    def close(self) -> None:
        """Close vector store connection"""
        self.client.close()
        self.logger.info("Vector store connection closed")