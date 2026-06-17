"""
Main RAG service orchestrating all components
"""

from typing import Dict, Any, List, Optional
import time
from source.utils.logger import get_logger
from source.utils.config import get_config
from source.embeddings.embedder import EmbeddingService
from source.embeddings.embedding_cache import EmbeddingCache
from source.vectordb.vector_store import VectorStore
from source.retrieval.retriever import LegalRetriever
from source.retrieval.reranker import CrossEncoderReranker
from source.llm.llm_client import LLMClient
from source.llm.output_parser import OutputParser
from source.prompts.prompt_templates import PromptTemplates
from source.services.cache_service import CacheService
from source.services.chat_history import ChatHistoryService

logger = get_logger(__name__)


class RAGService:
    """
    Main RAG service orchestrating the entire pipeline.
    """
    
    def __init__(self):
        """Initialize RAG service"""
        self.config = get_config()
        self.logger = logger
        
        # Initialize components
        self.embedding_cache = EmbeddingCache()
        self.embedding_service = EmbeddingService(cache=self.embedding_cache)
        self.vector_store = VectorStore()
        self.reranker = CrossEncoderReranker()
        self.retriever = LegalRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            reranker=self.reranker
        )
        self.llm_client = LLMClient()
        self.output_parser = OutputParser()
        self.prompt_templates = PromptTemplates()
        self.cache_service = CacheService()
        self.chat_history = ChatHistoryService()
        
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize all services"""
        self.logger.info("Initializing RAG service...")
        
        # Initialize vector store
        self.vector_store.initialize(recreate=False)
        
        # Initialize cache
        await self.cache_service.connect()
        await self.embedding_cache.connect()
        
        # Initialize chat history
        await self.chat_history.initialize()
        
        self.initialized = True
        self.logger.info("RAG service initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown all services"""
        self.logger.info("Shutting down RAG service...")
        
        await self.cache_service.close()
        await self.embedding_cache.close()
        await self.chat_history.close()
        self.vector_store.close()
        
        self.logger.info("RAG service shutdown complete")
    
    async def process_query(
        self,
        query: str,
        code_filter: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user query through RAG pipeline.
        
        Args:
            query: User query
            code_filter: Optional legal code filter
            chat_id: Optional chat session ID
        
        Returns:
            Response dictionary
        """
        start_time = time.time()
        
        # Check cache
        cache_key = f"query:{hash(query + str(code_filter))}"
        cached_response = await self.cache_service.get("response", cache_key)
        if cached_response:
            self.logger.info("Cache hit for query")
            return cached_response
        
        # Detect legal code if not specified
        if not code_filter:
            code_filter = await self.retriever.detect_legal_code(query)
        
        # Retrieve relevant documents
        retrieval_result = await self.retriever.retrieve_with_context(
            query=query,
            code_filter=code_filter,
            top_k=self.config.retrieval.get("top_k", 5)
        )
        
        # Extract content and sources
        context_chunks = [
            result["content"] 
            for result in retrieval_result["results"]
        ]
        sources = [
            {
                "code_name": r["code_name"],
                "code_short": r["code_short"],
                "article_number": r["article_number"],
                "score": r["score"]
            }
            for r in retrieval_result["results"]
        ]
        
        # Generate answer
        system_prompt = self.prompt_templates.get_system_prompt()
        qa_prompt = self.prompt_templates.get_qa_prompt(
            query=query,
            context_chunks=context_chunks
        )
        
        answer = ""
        async for chunk in self.llm_client.generate_response(
            prompt=qa_prompt,
            system_prompt=system_prompt,
            stream=True
        ):
            answer += chunk
        
        # Extract citations
        citations = self.output_parser.extract_citations(answer)
        
        # Clean answer
        answer = self.output_parser.clean_response(answer)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Build response
        response = {
            "answer": answer,
            "citations": citations,
            "sources": sources,
            "query": query,
            "chat_id": chat_id,
            "processing_time_ms": processing_time,
            "code_filter": code_filter
        }
        
        # Cache response
        await self.cache_service.set(
            "response",
            cache_key,
            response,
            ttl=3600  # 1 hour
        )
        
        # Save to chat history
        if chat_id:
            await self.chat_history.save_message(
                chat_id=chat_id,
                query=query,
                answer=answer,
                citations=citations,
                sources=sources,
                processing_time_ms=processing_time
            )
        
        return response
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG service statistics.
        
        Returns:
            Statistics dictionary
        """
        vector_stats = self.vector_store.get_stats()
        
        return {
            "total_documents": vector_stats.get("points_count", 0),
            "total_chunks": vector_stats.get("vectors_count", 0),
            "legal_codes": [
                code["name"] 
                for code in self.config.legal_codes
            ],
            "last_updated": None,
            "vector_db": vector_stats
        }
    
    async def ingest_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Ingest documents into the system.
        
        Args:
            documents: List of document dictionaries
        
        Returns:
            Ingestion statistics
        """
        from source.ingestion.parser import LegalDocumentParser
        from source.chunking.chunker import ArticleChunker
        from source.chunking.metadata_enricher import MetadataEnricher
        
        parser = LegalDocumentParser()
        chunker = ArticleChunker()
        enricher = MetadataEnricher()
        
        total_articles = 0
        total_chunks = 0
        
        for doc in documents:
            # Parse document
            articles = parser.parse_document(
                content=doc["content"],
                metadata=doc["metadata"]
            )
            total_articles += len(articles)
            
            # Chunk articles
            chunks = chunker.chunk_articles(articles)
            
            # Enrich metadata
            enriched_chunks = enricher.batch_enrich(chunks)
            total_chunks += len(enriched_chunks)
            
            # Generate embeddings
            texts = [chunk["content"] for chunk in enriched_chunks]
            embeddings = await self.embedding_service.embed_texts(
                texts,
                show_progress=True
            )
            
            # Upsert to vector store
            await self.vector_store.upsert(
                chunks=enriched_chunks,
                embeddings=embeddings
            )
        
        return {
            "documents_processed": len(documents),
            "articles_extracted": total_articles,
            "chunks_created": total_chunks
        }