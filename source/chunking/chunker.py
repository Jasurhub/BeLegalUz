# src/chunking/chunker.py
import uuid
import re
from typing import List, Dict, Any
from source.utils.logger import get_logger
from source.utils.config import get_config

logger = get_logger(__name__)


class ArticleChunker:
    """Article-level chunking for legal documents"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logger
        self.strategy = self.config.chunking.get("strategy", "article_level")
    
    def chunk_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process articles into chunks"""
        self.logger.info(f"Chunking {len(articles)} articles using {self.strategy} strategy")
        
        if self.strategy == "article_level":
            return self._article_level_chunking(articles)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")

    def _article_level_chunking(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Har bir moddani alohida chunk qilish, lekin katta moddalarni bo'lish"""
        chunks = []
        max_chunk_size = 3000  # maksimal chunk hajmi (belgilar)

        for article in articles:
            content = article["text"]

            # Agar modda juda katta bo'lsa, qismlarga bo'lish
            if len(content) > max_chunk_size:
                sub_chunks = self._split_large_article(article, max_chunk_size)
                chunks.extend(sub_chunks)
            else:
                # Oddiy chunk
                chunk_uuid = str(uuid.uuid4())
                chunk = {
                    "id": chunk_uuid,
                    "content": content,
                    "metadata": {
                        "code_name": article["code_name"],
                        "code_short": article["code_short"],
                        "article_number": article["article_number"],
                        "chapter": article.get("chapter"),
                        "title": article.get("title", ""),
                        "chunk_type": "article",
                        "is_active": article.get("is_active", True),
                    }
                }
                chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def _split_large_article(self, article: Dict[str, Any], max_size: int) -> List[Dict[str, Any]]:
        """Katta moddani qismlarga bo'lish (qism raqamlari bilan)"""
        content = article["text"]
        chunks = []

        # Qismlarni topish (1-qism, 2-qism, va h.k.)
        part_pattern = re.compile(r'(\d+)-qism[.:]?\s*(.*?)(?=\n\d+-qism[.:]?|\Z)', re.DOTALL)
        matches = list(part_pattern.finditer(content))

        if matches:
            # Har bir qismni alohida chunk qilish
            for i, match in enumerate(matches):
                part_num = match.group(1)
                part_content = match.group(2).strip()

                chunk_uuid = str(uuid.uuid4())
                chunk = {
                    "id": chunk_uuid,
                    "content": f"{article['article_number']}-modda, {part_num}-qism.\n{part_content}",
                    "metadata": {
                        "code_name": article["code_name"],
                        "code_short": article["code_short"],
                        "article_number": article["article_number"],
                        "part_number": part_num,
                        "chapter": article.get("chapter"),
                        "title": article.get("title", ""),
                        "chunk_type": "article_part",
                        "is_active": article.get("is_active", True),
                    }
                }
                chunks.append(chunk)
        else:
            # Agar qismlar topilmasa, oddiy bo'lish
            parts = self._split_by_sentences(content, max_size)
            for i, part in enumerate(parts, 1):
                chunk_uuid = str(uuid.uuid4())
                chunk = {
                    "id": chunk_uuid,
                    "content": part,
                    "metadata": {
                        "code_name": article["code_name"],
                        "code_short": article["code_short"],
                        "article_number": article["article_number"],
                        "part_number": str(i),
                        "chapter": article.get("chapter"),
                        "title": article.get("title", ""),
                        "chunk_type": "article_part",
                        "is_active": article.get("is_active", True),
                    }
                }
                chunks.append(chunk)

        return chunks

    def _split_by_sentences(self, text: str, max_size: int) -> List[str]:
        """Matnni gaplar bo'yicha bo'lish"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks