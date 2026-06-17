# src/ingestion/parser.py
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from source.utils.logger import get_logger
from source.utils.config import get_config

logger = get_logger(__name__)


class LegalDocumentParser:
    def __init__(self):
        self.config = get_config()
        self.legal_codes = {
            code["short_code"]: code
            for code in self.config.legal_codes
        }
        self.logger = logger

    def parse_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Asosiy parse qilish funksiyasi"""
        code_info = self._detect_legal_code(metadata, content)

        # HTML tozalash
        if self._is_html_content(content):
            content = self._clean_html_to_text(content)
        else:
            content = self._clean_text(content)

        articles = self._extract_articles(content, code_info)
        self.logger.info(f"Parsed {len(articles)} articles from {code_info.get('name', 'Unknown')}")
        return articles

    def _is_html_content(self, content: str) -> bool:
        """Kontent HTML yoki TXT ekanligini aniqlash"""
        html_indicators = ['<div', '<p>', '</p>', '<span', '<html', '<body']
        content_lower = content[:5000].lower()
        return any(indicator in content_lower for indicator in html_indicators)

    def _clean_text(self, text: str) -> str:
        """Matndagi ortiqcha belgilarni tozalash"""
        text = text.replace('\t', ' ')
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _clean_html_to_text(self, html_content: str) -> str:
        """HTML teglarni olib tashlab, faqat toza matn qoldirish"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Ortiqcha teglarni o'chirish
        for tag in soup(['script', 'style', 'meta', 'link', 'head', 'title', 'a']):
            tag.decompose()

        # Matnni olish
        text = soup.get_text(separator='\n', strip=True)

        # HTML entity'larni tozalash
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')

        # Qatorlarni tozalash
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.replace('\t', ' ')
        text = re.sub(r' +', ' ', text)

        return text.strip()

    def _detect_legal_code(self, metadata: Dict[str, Any], content: str) -> Dict[str, str]:
        filename = metadata.get("filename", "").lower()

        # Fayl nomidan aniqlash
        for short_code, code_info in self.legal_codes.items():
            pattern = code_info.get("file_pattern", "")
            if pattern and re.search(pattern, filename, re.IGNORECASE):
                return code_info

        # Kontentdan aniqlash
        content_sample = content[:3000]
        for short_code, code_info in self.legal_codes.items():
            if code_info["name"] in content_sample:
                return code_info

        return {"name": "Noma'lum kodeks", "short_code": "UNKNOWN", "file_pattern": ""}

    def _extract_articles(self, content: str, code_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """Moddalarni ajratib olish - barcha moddalarni saqlash"""
        articles = []
        current_chapter = "Umumiy qoidalar"

        # Superscript raqamlar bilan moddalarni topish
        article_pattern = re.compile(
            r'(?m)(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?)\s*-\s*modda\s*[.:]?\s*(.*?)(?=\n\s*\d+(?:[⁰¹²³⁴⁵⁶⁸⁹]+)?\s*-\s*modda|\Z)',
            re.IGNORECASE | re.DOTALL
        )

        matches = list(article_pattern.finditer(content))

        self.logger.info(f"Jami {len(matches)} ta modda topildi (shu jumladan superscript'li)")

        for i, match in enumerate(matches):
            article_num = match.group(1)
            article_content = match.group(2).strip() if len(match.groups()) > 1 else ""

            # Sarlavha va matnni ajratish
            lines = article_content.split('\n', 1)
            if len(lines) > 1:
                article_title = lines[0].strip()
                article_text = lines[1].strip()
            else:
                article_title = ""
                article_text = article_content

            # Bob o'zgarishini tekshirish
            chapter_match = re.search(
                r'(?m)(\d+)\s*-\s*bob\s*[.:]?\s*(.+?)(?=\n)',
                article_text,
                re.IGNORECASE
            )
            if chapter_match:
                current_chapter = chapter_match.group(2).strip()
                article_text = article_text[chapter_match.end():].strip()

            # Matnni tozalash
            clean_content = re.sub(r'\s+', ' ', article_text).strip()

            # ⭐ MUHIM: BARCHA moddalarni saqlash (hatto qisqa bo'lsa ham!)
            # Faqat butunlay bo'sh moddalarni o'tkazib yuboramiz
            if clean_content and len(clean_content) > 5:  # Minimal uzunlikni 5 ga tushirdim
                articles.append({
                    "code_name": code_info["name"],
                    "code_short": code_info["short_code"],
                    "article_number": article_num,
                    "chapter": current_chapter,
                    "title": article_title,
                    "text": clean_content,
                    "is_active": True
                })

        # Statistika
        regular_articles = len(
            [a for a in articles if not any(c.isupper() for c in a['article_number'] if c.isdigit() == False)])
        superscript_articles = len(articles) - regular_articles

        self.logger.info(f"✅ Asosiy moddalar: {regular_articles}")
        if superscript_articles > 0:
            self.logger.info(f"   Superscript'li moddalar: {superscript_articles}")
        self.logger.info(f"   Jami: {len(articles)}")

        return articles

    def _extract_articles_simple(
            self,
            content: str,
            matches: List[re.Match],
            code_info: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Eng sodda regex bilan moddalarni ajratish"""
        articles = []
        current_chapter = "Umumiy qoidalar"

        for i, match in enumerate(matches):
            article_num = match.group(1)

            # Modda matnini ajratish
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)

            raw_content = content[start_pos:end_pos]

            # Bob o'zgarishini tekshirish
            chapter_match = re.search(
                r'(?m)(\d+)\s*[-–—]\s*bob\s*[.:]?\s*(.+?)(?=\n)',
                raw_content,
                re.IGNORECASE
            )
            if chapter_match:
                current_chapter = chapter_match.group(2).strip()

            # Matnni tozalash
            clean_content = re.sub(r'\s+', ' ', raw_content).strip()

            # Sarlavha va matnni ajratish
            lines = clean_content.split('.', 1)
            if len(lines) > 1:
                article_title = lines[0].strip()
                article_text = lines[1].strip()
            else:
                article_title = ""
                article_text = clean_content

            # Qisqa moddalarni o'tkazib yuborish
            if len(article_text) > 20:
                articles.append({
                    "code_name": code_info["name"],
                    "code_short": code_info["short_code"],
                    "article_number": article_num,
                    "chapter": current_chapter,
                    "title": article_title,
                    "text": article_text,
                    "is_active": True
                })

        self.logger.info(f"Sodda regex bilan {len(articles)} ta modda topildi")
        return articles