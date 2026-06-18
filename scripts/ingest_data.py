#!/usr/bin/env python3
"""
Data ingestion script for legal documents
LOKAL - sentence-transformers ishlatadi
"""

import asyncio
import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from source.ingestion.loader import DocumentLoader
from source.ingestion.parser import LegalDocumentParser
from source.chunking.chunker import ArticleChunker
from source.chunking.metadata_enricher import MetadataEnricher
from source.embeddings.embedder import EmbeddingService
from source.vectordb.vector_store import VectorStore
from source.utils.config import load_config
from source.utils.logger import setup_logging, get_logger


async def ingest_documents(data_dir: str, recreate: bool = False):
    """
    Ingest documents from directory.

    Args:
        data_dir: Path to data directory
        recreate: Whether to recreate vector collection
    """
    # Setup
    load_config()
    setup_logging(log_level="INFO")
    logger = get_logger(__name__)

    logger.info(f"Starting ingestion from {data_dir}")
    logger.info(f"🤖 Embedding: Lokal sentence-transformers (multilingual-e5-large)")

    # Initialize components
    loader = DocumentLoader()
    parser = LegalDocumentParser()
    chunker = ArticleChunker()
    enricher = MetadataEnricher()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    # Initialize vector store
    vector_store.initialize(recreate=recreate)

    # Load documents
    documents = await loader.load_from_directory(data_dir)
    logger.info(f"Loaded {len(documents)} documents")

    # Process documents
    total_chunks = 0

    for doc in documents:
        logger.info(f"Processing: {doc['metadata']['filename']}")

        # Parse
        articles = parser.parse_document(
            content=doc["content"],
            metadata=doc["metadata"]
        )

        # Chunk
        chunks = chunker.chunk_articles(articles)

        # Enrich
        enriched_chunks = enricher.batch_enrich(chunks)

        # Generate embeddings - LOKAL
        texts = [chunk["content"] for chunk in enriched_chunks]
        embeddings = await embedding_service.embed_texts(
            texts,
            show_progress=True
        )

        # Upsert
        await vector_store.upsert(
            chunks=enriched_chunks,
            embeddings=embeddings
        )

        total_chunks += len(enriched_chunks)

    # Stats
    stats = vector_store.get_stats()
    logger.info(f"🎉 Ingestion complete!")
    logger.info(f"📊 Total chunks: {total_chunks}")
    logger.info(f"📈 Vector store stats: {stats}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ingest legal documents into vector database (LOKAL)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data/codes",
        help="Path to data directory"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate vector collection"
    )

    args = parser.parse_args()

    asyncio.run(ingest_documents(args.data_dir, args.recreate))


if __name__ == "__main__":
    main()