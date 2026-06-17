# src/vectordb/collection_manager.py
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    CollectionInfo,
    PayloadSchemaType
)
from source.utils.logger import get_logger
from source.utils.config import get_config

logger = get_logger(__name__)


class CollectionManager:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.config = get_config()
        self.logger = logger

        self.collection_name = self.config.vectordb.get(
            "collection_name", "uzbek_legal_codes"
        )
        self.vector_size = self.config.embedding.get("dimension", 1024)
        self.distance = self.config.vectordb.get("distance", "cosine")

    def collection_exists(self) -> bool:
        try:
            collections = self.client.get_collections().collections
            return any(col.name == self.collection_name for col in collections)
        except Exception as e:
            self.logger.error(f"Error checking collection: {e}")
            return False

    def create_collection(self, recreate: bool = False) -> bool:
        try:
            if self.collection_exists():
                if recreate:
                    self.logger.info(f"Recreating collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    self.logger.info(f"Collection already exists: {self.collection_name}")
                    return True

            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "dot": Distance.DOT
            }
            distance = distance_map.get(self.distance.lower(), Distance.COSINE)

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=distance
                )
            )

            # Indexlarni to'g'ri yaratish
            self._create_payload_indexes()

            self.logger.info(f"Collection created: {self.collection_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            return False

    def _create_payload_indexes(self) -> None:
        """Qdrant uchun to'g'ri indexlar yaratish"""
        indexes = [
            ("code_short", PayloadSchemaType.KEYWORD),
            ("code_name", PayloadSchemaType.KEYWORD),
            ("article_number", PayloadSchemaType.KEYWORD),
            ("is_active", PayloadSchemaType.BOOL),
            ("chunk_type", PayloadSchemaType.KEYWORD),
        ]

        for field_name, field_type in indexes:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                self.logger.debug(f"Created index for {field_name}")
            except Exception as e:
                self.logger.warning(f"Index creation failed for {field_name}: {e}")

    def get_collection_info(self) -> Optional[CollectionInfo]:
        try:
            if self.collection_exists():
                return self.client.get_collection(self.collection_name)
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
        return None

    def delete_collection(self) -> bool:
        try:
            if self.collection_exists():
                self.client.delete_collection(self.collection_name)
                self.logger.info(f"Collection deleted: {self.collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting collection: {e}")
            return False

    def get_stats(self) -> dict:
        info = self.get_collection_info()
        if info:
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status)
            }
        return {}