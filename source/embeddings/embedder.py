"""
Embedding service for multilingual text encoding
"""

import asyncio
from typing import List, Optional, Union, TYPE_CHECKING
import numpy as np
from sentence_transformers import SentenceTransformer
from source.utils.logger import get_logger
from source.utils.config import get_config

# Forward reference uchun TYPE_CHECKING ishlatamiz (circular import oldini olish)
if TYPE_CHECKING:
    from source.embeddings.embedding_cache import EmbeddingCache

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using multilingual models.
    Supports batching and caching for efficiency.
    """
    
    def __init__(self, cache: Optional["EmbeddingCache"] = None):
        """
        Initialize embedding service.
        
        Args:
            cache: Optional embedding cache
        """
        self.config = get_config()
        self.logger = logger
        self.cache = cache
        
        # Configuration
        self.model_name = self.config.embedding.get(
            "model_name", "intfloat/multilingual-e5-large"
        )
        self.device = self.config.embedding.get("device", "cpu")
        self.batch_size = self.config.embedding.get("batch_size", 32)
        self.normalize = self.config.embedding.get("normalize", True)
        
        # Load model
        self._model: Optional[SentenceTransformer] = None
        self.logger.info(f"Initializing embedding model: {self.model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True
            )
            self.logger.info(f"Embedding model loaded on {self.device}")
        return self._model
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.config.embedding.get("dimension", 1024)
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector as list of floats
        """
        # Check cache
        if self.cache:
            cached = await self.cache.get(text)
            if cached is not None:
                self.logger.debug("Embedding cache hit")
                return cached
        
        # Generate embedding
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._generate_embedding(text)
        )
        
        # Cache result
        if self.cache:
            await self.cache.set(text, embedding)
        
        return embedding
    
    async def embed_texts(
        self, 
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            show_progress: Whether to show progress bar
        
        Returns:
            List of embedding vectors
        """
        self.logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Check cache for all texts
        cached_embeddings = {}
        texts_to_compute = []
        
        if self.cache:
            for text in texts:
                cached = await self.cache.get(text)
                if cached is not None:
                    cached_embeddings[text] = cached
                else:
                    texts_to_compute.append(text)
        else:
            texts_to_compute = texts
        
        # Compute missing embeddings
        if texts_to_compute:
            loop = asyncio.get_event_loop()
            new_embeddings = await loop.run_in_executor(
                None,
                lambda: self._generate_embeddings_batch(texts_to_compute, show_progress)
            )
            
            # Cache new embeddings
            if self.cache:
                for text, embedding in zip(texts_to_compute, new_embeddings):
                    await self.cache.set(text, embedding)
            
            # Combine cached and new embeddings
            all_embeddings = []
            new_idx = 0
            for text in texts:
                if text in cached_embeddings:
                    all_embeddings.append(cached_embeddings[text])
                else:
                    all_embeddings.append(new_embeddings[new_idx])
                    new_idx += 1
        else:
            # All cached
            all_embeddings = [cached_embeddings[text] for text in texts]
        
        self.logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text (sync).
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
            show_progress_bar=False
        )
        return embedding[0].tolist()
    
    def _generate_embeddings_batch(
        self, 
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for batch of texts (sync).
        
        Args:
            texts: List of input texts
            show_progress: Whether to show progress bar
        
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
            show_progress_bar=show_progress,
            batch_size=self.batch_size
        )
        return embeddings.tolist()
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Cosine similarity score
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (
            np.linalg.norm(vec1) * np.linalg.norm(vec2)
        )
        return float(similarity)