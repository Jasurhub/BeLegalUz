"""
Document loader for legal documents
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Union
import aiofiles
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from source.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """
    Asynchronous document loader supporting PDF, HTML, and DOCX formats.
    """

    def __init__(self, supported_extensions: Optional[List[str]] = None):
        """
        Initialize document loader.

        Args:
            supported_extensions: List of supported file extensions
        """
        self.supported_extensions = supported_extensions or [
            ".pdf", ".html", ".htm", ".docx", ".txt"
        ]
        self.logger = logger

    async def load_from_directory(
        self,
        directory_path: Union[str, Path],
        recursive: bool = True
    ) -> List[dict]:
        """
        Load all documents from a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively

        Returns:
            List of document dictionaries with metadata
        """
        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        documents = []

        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")

        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    doc = await self.load_document(file_path)
                    if doc:
                        documents.append(doc)
                        self.logger.info(f"Loaded document: {file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to load {file_path}: {str(e)}")

        self.logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents

    async def load_document(self, file_path: Union[str, Path]) -> Optional[dict]:
        """
        Load a single document.

        Args:
            file_path: Path to document

        Returns:
            Document dictionary with content and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.logger.debug(f"Loading document: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return await self._load_pdf(file_path)
        elif suffix in [".html", ".htm"]:
            return await self._load_html(file_path)
        elif suffix == ".docx":
            return await self._load_docx(file_path)
        elif suffix == ".txt":
            return await self._load_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    async def _load_pdf(self, file_path: Path) -> dict:
        """Load PDF document"""
        loop = asyncio.get_event_loop()

        def _extract_pdf():
            doc = fitz.open(file_path)
            text = ""
            metadata = doc.metadata

            for page in doc:
                text += page.get_text()

            doc.close()
            return text, metadata

        text, metadata = await loop.run_in_executor(None, _extract_pdf)

        return {
            "content": text,
            "metadata": {
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": "pdf",
                "total_pages": metadata.get("pages", 0),
                **metadata
            }
        }

    async def _load_html(self, file_path: Path) -> dict:
        """Load HTML document"""
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()

        soup = BeautifulSoup(content, "lxml")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator="\n", strip=True)

        return {
            "content": text,
            "metadata": {
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": "html",
                "title": soup.title.string if soup.title else None
            }
        }

    async def _load_docx(self, file_path: Path) -> dict:
        """Load DOCX document"""
        from docx import Document

        loop = asyncio.get_event_loop()

        def _extract_docx():
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text

        text = await loop.run_in_executor(None, _extract_docx)

        return {
            "content": text,
            "metadata": {
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": "docx"
            }
        }

    # src/ingestion/loader.py ichidagi _load_txt funksiyasi
    async def _load_txt(self, file_path: Path) -> dict:
        """Load plain text document with SMART encoding detection"""

        # Avval faylni binary o'qib, encoding ni aniqlash
        async with aiofiles.open(file_path, "rb") as f:
            binary_content = await f.read()

        # Encoding larni sinab ko'rish (eng yaxshisidan boshlab)
        encodings = [
            'utf-8',
            'utf-8-sig',  # BOM bilan UTF-8
            'cp1252',  # Windows Western (ko'p hollarda to'g'ri)
            'cp1251',  # Windows Cyrillic
            'iso-8859-1',  # Latin-1
            'koi8-r',  # Russian
        ]

        content = None
        used_encoding = None

        for encoding in encodings:
            try:
                content = binary_content.decode(encoding)
                # Tekshirish: agar matnda ko'p "?" yoki g'alati belgilar bo'lsa, bu encoding noto'g'ri
                if '?' in content[:1000] and encoding == 'iso-8859-1':
                    continue
                used_encoding = encoding
                self.logger.info(f"Loaded {file_path.name} with encoding: {encoding}")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        # Agar hech qaysi encoding ishlamasa
        if content is None:
            content = binary_content.decode('utf-8', errors='ignore')
            used_encoding = 'utf-8 (fallback)'
            self.logger.warning(f"Could not decode {file_path.name}, used utf-8 with ignore")

        return {
            "content": content,
            "metadata": {
                "source": str(file_path),
                "filename": file_path.name,
                "file_type": "txt",
                "encoding": used_encoding
            }
        }