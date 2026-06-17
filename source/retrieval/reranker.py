"""
Cross-encoder reranker for improving retrieval results
"""

from typing import List, Tuple, Optional
from source.utils.logger import get_logger
from source.utils.config import get_config
from source.vectordb.schema import ChunkPayload

logger = get_logger(__name__)


class CrossEncoderReranker:
    """
    Reranks retrieval results using a cross-encoder model.
    Provides more accurate ranking than vector similarity alone.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize reranker.

        Args:
            enabled: Whether to enable reranking
        """
        self.config = get_config()
        self.logger = logger
        self.enabled = enabled and self.config.retrieval.get("enable_reranking", False)

        if self.enabled:
            try:
                from sentence_transformers import CrossEncoder
                self.model_name = "cross-encoder/multilingual-ms-marco-MiniLM-L-6-v2"
                self.model = CrossEncoder(self.model_name)
                self.logger.info(f"Cross-encoder reranker loaded: {self.model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load cross-encoder: {e}. Reranking disabled.")
                self.enabled = False
                self.model = None
        else:
            self.model = None

    async def rerank(
        self,
        query: str,
        results: List[Tuple[ChunkPayload, float]],
        top_k: int = 5
    ) -> List[Tuple[ChunkPayload, float]]:
        """
        Rerank retrieval results using cross-encoder.

        Args:
            query: User query
            results: List of (payload, score) tuples
            top_k: Number of results to return

        Returns:
            Reranked list of (payload, score) tuples
        """
        if not self.enabled or not self.model or len(results) == 0:
            # Return original results if reranking is disabled
            return results[:top_k]

        self.logger.info(f"Reranking {len(results)} results")

        # Prepare pairs for cross-encoder
        pairs = [[query, payload.content] for payload, _ in results]

        # Get cross-encoder scores
        try:
            scores = self.model.predict(pairs)

            # Combine with original scores
            reranked_results = []
            for (payload, original_score), new_score in zip(results, scores):
                # Average or weighted combination
                combined_score = (original_score + new_score) / 2
                reranked_results.append((payload, float(combined_score)))

            # Sort by combined score
            reranked_results.sort(key=lambda x: x[1], reverse=True)

            self.logger.info(f"Reranking complete. Top score: {reranked_results[0][1]:.4f}")
            return reranked_results[:top_k]

        except Exception as e:
            self.logger.error(f"Reranking failed: {e}. Returning original results.")
            return results[:top_k]

    def rerank_sync(
        self,
        query: str,
        results: List[Tuple[ChunkPayload, float]],
        top_k: int = 5
    ) -> List[Tuple[ChunkPayload, float]]:
        """
        Synchronous version of rerank.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.rerank(query, results, top_k))