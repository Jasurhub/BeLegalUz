"""
Legal document retriever with metadata filtering
"""

from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from source.utils.logger import get_logger
from source.utils.config import get_config
from source.embeddings.embedder import EmbeddingService
from source.vectordb.vector_store import VectorStore
from source.vectordb.schema import ChunkPayload

# Forward reference
if TYPE_CHECKING:
    from source.retrieval.reranker import CrossEncoderReranker

logger = get_logger(__name__)


class LegalRetriever:
    """
    Retriever for legal documents with advanced filtering and ranking.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        reranker: Optional["CrossEncoderReranker"] = None
    ):
        """Initialize legal retriever."""
        self.config = get_config()
        self.logger = logger
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranker = reranker

    async def retrieve(
        self,
        query: str,
        code_filter: Optional[str] = None,
        top_k: int = 10  # ← 5 dan 10 ga oshirildi
    ) -> List[Tuple[ChunkPayload, float]]:
        """
        Retrieve relevant legal documents.

        Args:
            query: User query
            code_filter: Optional legal code filter (e.g., "MK", "JK")
            top_k: Number of results to return

        Returns:
            List of (payload, score) tuples
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # Build metadata filter
        metadata_filter = {"is_active": True}
        if code_filter and code_filter != "null":
            metadata_filter["code_short"] = code_filter.upper()

        # ⭐ MUHIM: score_threshold ni 0.5 ga tushirish
        score_threshold = self.config.retrieval.get("score_threshold", 0.5)

        # Search vector store - ko'proq natija olish
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more for reranking
            metadata_filter=metadata_filter,
            score_threshold=score_threshold
        )

        self.logger.info(f"Retrieved {len(results)} raw results (threshold: {score_threshold})")

        # Apply reranking if enabled
        if self.reranker and len(results) > 0:
            results = await self.reranker.rerank(query, results, top_k)
        else:
            results = results[:top_k]

        self.logger.info(f"Final results: {len(results)} for query: {query[:50]}...")
        return results

    async def detect_legal_code(self, query: str) -> Optional[str]:
        """
        Detect which legal code the query is about.
        """
        # Kengaytirilgan kalit so'zlar
        code_keywords = {
            # Mehnat
            "mehnat": "MK",
            "ish": "MK",
            "ta'til": "MK",
            "ish haqi": "MK",
            "maosh": "MK",
            "ish beruvchi": "MK",
            "xodim": "MK",
            # Jinoyat
            "jinoyat": "JK",
            "jazo": "JK",
            "qamoq": "JK",
            "og'irlik": "JK",
            "o'g'irlik": "JK",
            # Soliq
            "soliq": "SK",
            "vergi": "SK",
            "qqs": "SK",
            "qqS": "SK",
            "solik": "SK",
            # Fuqarolik
            "fuqarolik": "FK",
            "shartnoma": "FK",
            "mulkiy": "FK",
            # Oila
            "oila": "OK",
            "nikoh": "OK",
            "ajrim": "OK",
            "aliment": "OK",
            # Ma'muriy
            "ma'muriy": "MJK",
            "jarima": "MJK",
            # Konstitutsiya
            "konstitutsiya": "KONST",
            "asosiy": "KONST",
        }

        query_lower = query.lower()

        for keyword, code in code_keywords.items():
            if keyword in query_lower:
                self.logger.debug(f"Detected legal code: {code} from keyword: {keyword}")
                return code

        return None

    async def retrieve_with_context(
        self,
        query: str,
        code_filter: Optional[str] = None,
        top_k: int = 10  # ← 5 dan 10 ga oshirildi
    ) -> Dict[str, Any]:
        """
        Retrieve documents with additional context information.
        """
        results = await self.retrieve(query, code_filter, top_k)

        # Format results
        formatted_results = []
        for payload, score in results:
            formatted_results.append({
                "content": payload.content,
                "code_name": payload.code_name,
                "code_short": payload.code_short,
                "article_number": payload.article_number,
                "chapter": payload.chapter,
                "score": score
            })

        return {
            "results": formatted_results,
            "query": query,
            "code_filter": code_filter,
            "total_results": len(formatted_results)
        }