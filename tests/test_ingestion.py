"""
Tests for document ingestion pipeline (Loader and Parser)
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from source.ingestion.loader import DocumentLoader
from source.ingestion.parser import LegalDocumentParser


@pytest.fixture
def loader():
    return DocumentLoader()


@pytest.fixture
def parser():
    # Mock config to avoid loading actual yaml in tests
    with patch('src.ingestion.parser.get_config') as mock_config:
        mock_config.return_value.legal_codes = [
            {"name": "Mehnat kodeksi", "short_code": "MK", "file_pattern": "mehnat*"}
        ]
        mock_config.return_value.chunking = {"min_article_length": 10}
        yield LegalDocumentParser()


@pytest.mark.asyncio
async def test_load_txt_document(loader, tmp_path):
    """Test loading a plain text document"""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Bu test matni.", encoding="utf-8")
    
    doc = await loader.load_document(txt_file)
    
    assert doc is not None
    assert doc["content"] == "Bu test matni."
    assert doc["metadata"]["file_type"] == "txt"


@pytest.mark.asyncio
async def test_load_from_directory(loader, tmp_path):
    """Test loading multiple documents from a directory"""
    (tmp_path / "doc1.txt").write_text("Matn 1", encoding="utf-8")
    (tmp_path / "doc2.txt").write_text("Matn 2", encoding="utf-8")
    
    docs = await loader.load_from_directory(tmp_path, recursive=False)
    
    assert len(docs) == 2


def test_parse_document_articles(parser):
    """Test extracting articles from legal text"""
    content = """
    1-bob. Umumiy qoidalar
    
    1-modda. Kodeksning maqsadi
    Ushbu Kodeksning maqsadi munosabatlarni tartibga solishdir.
    
    2-modda. Qo'llanish sohasi
    Ushbu Kodeks barcha fuqarolarga nisbatan qo'llaniladi.
    """
    
    metadata = {"filename": "mehnat_kodeksi.pdf"}
    articles = parser.parse_document(content, metadata)
    
    assert len(articles) == 2
    assert articles[0]["article_number"] == "1"
    assert articles[1]["article_number"] == "2"
    assert articles[0]["code_short"] == "MK"