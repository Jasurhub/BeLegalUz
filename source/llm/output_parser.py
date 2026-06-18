"""
Parser for LLM output extraction
"""

import json
import re
from typing import List, Dict, Optional, Any
from source.utils.logger import get_logger

logger = get_logger(__name__)


class OutputParser:
    """
    Parses and extracts structured data from LLM responses.
    """
    
    def __init__(self):
        """Initialize parser"""
        self.logger = logger
    
    def extract_citations(self, text: str) -> List[Dict[str, str]]:
        """
        Extract legal citations from text.
        
        Args:
            text: LLM response text
        
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        # ⭐ Pattern 1: "Soliq kodeksining 163-moddasiga" yoki "Soliq kodeksi, 163-modda"
        pattern1 = re.compile(
            r"([A-Za-z\u0027\u2019\s]+)\s+kodeks(?:i|ining)?[,\s]+(?:\*\*)?(\d+(?:[¹²³⁴⁵⁶⁷⁸⁹]+)?)(?:-modda|-moddasi)?",
            re.IGNORECASE
        )

        # ⭐ Pattern 2: "**163-modda**" yoki "163-modda"
        pattern2 = re.compile(
            r"\*{0,2}(\d+(?:[¹²³⁴⁵⁶⁷⁸⁹]+)?)\s*-?\s*modda\*{0,2}",
            re.IGNORECASE
        )

        # ⭐ Pattern 3: "Modda 163"
        pattern3 = re.compile(
            r"modda\s+(\d+)",
            re.IGNORECASE
        )

        # ⭐ Pattern 4: "SK 163-modda" yoki "JK 128¹-modda"
        pattern4 = re.compile(
            r"\b(MK|JK|FK|SK|MJK|OK|JPK|FPK|IPK|KONST)\s+(\d+(?:[¹²³⁴⁵⁶⁷⁸⁹]+)?)(?:-modda)?",
            re.IGNORECASE
        )

        # Kodeks nomlarini to'liq nomlarga aylantirish
        code_name_map = {
            "soliq": "O'zbekiston Respublikasi Soliq kodeksi",
            "jinoyat": "O'zbekiston Respublikasi Jinoyat kodeksi",
            "fuqarolik": "O'zbekiston Respublikasi Fuqarolik kodeksi",
            "mehnat": "O'zbekiston Respublikasi Mehnat kodeksi",
            "oila": "O'zbekiston Respublikasi Oila kodeksi",
            "ma'muriy": "O'zbekiston Respublikasi Ma'muriy javobgarlik to'g'risidagi kodeksi",
            "jinoyat-protsessual": "O'zbekiston Respublikasi Jinoyat-protsessual kodeksi",
            "fuqarolik protsessual": "O'zbekiston Respublikasi Fuqarolik protsessual kodeksi",
            "iqtisodiy": "O'zbekiston Respublikasi Iqtisodiy protsessual kodeksi",
            "konstitutsiya": "O'zbekiston Respublikasi Konstitutsiyasi",
        }

        # Short code to full name
        short_code_map = {
            "MK": "O'zbekiston Respublikasi Mehnat kodeksi",
            "JK": "O'zbekiston Respublikasi Jinoyat kodeksi",
            "FK": "O'zbekiston Respublikasi Fuqarolik kodeksi",
            "SK": "O'zbekiston Respublikasi Soliq kodeksi",
            "MJK": "O'zbekiston Respublikasi Ma'muriy javobgarlik to'g'risidagi kodeksi",
            "OK": "O'zbekiston Respublikasi Oila kodeksi",
            "JPK": "O'zbekiston Respublikasi Jinoyat-protsessual kodeksi",
            "FPK": "O'zbekiston Respublikasi Fuqarolik protsessual kodeksi",
            "IPK": "O'zbekiston Respublikasi Iqtisodiy protsessual kodeksi",
            "KONST": "O'zbekiston Respublikasi Konstitutsiyasi",
        }

        # Pattern 1: "Soliq kodeksining 163-moddasi"
        for match in pattern1.finditer(text):
            code_name_raw = match.group(1).strip().lower()
            article_number = match.group(2).strip()

            # To'liq nomni topish
            code_name_full = None
            for key, full_name in code_name_map.items():
                if key in code_name_raw:
                    code_name_full = full_name
                    break

            if code_name_full:
                citations.append({
                    "code_name": code_name_full,
                    "article_number": article_number
                })
                self.logger.debug(f"Pattern 1 match: {code_name_full}, {article_number}")

        # Pattern 2: "**163-modda**" - faqat article_number
        for match in pattern2.finditer(text):
            article_number = match.group(1).strip()

            # Agar allaqachon qo'shilgan bo'lsa, o'tkazib yuborish
            already_added = any(c["article_number"] == article_number for c in citations)
            if not already_added:
                citations.append({
                    "code_name": "O'zbekiston Respublikasi qonunchiligi",
                    "article_number": article_number
                })
                self.logger.debug(f"Pattern 2 match: {article_number}")

        # Pattern 3: "Modda 163"
        for match in pattern3.finditer(text):
            article_number = match.group(1).strip()

            already_added = any(c["article_number"] == article_number for c in citations)
            if not already_added:
                citations.append({
                    "code_name": "O'zbekiston Respublikasi qonunchiligi",
                    "article_number": article_number
                })
                self.logger.debug(f"Pattern 3 match: {article_number}")

        # Pattern 4: "SK 163-modda"
        for match in pattern4.finditer(text):
            short_code = match.group(1).upper()
            article_number = match.group(2).strip()

            code_name_full = short_code_map.get(short_code, "O'zbekiston Respublikasi qonunchiligi")

            already_added = any(
                c["article_number"] == article_number and c.get("code_name") == code_name_full
                for c in citations
            )
            if not already_added:
                citations.append({
                    "code_name": code_name_full,
                    "code_short": short_code,
                    "article_number": article_number
                })
                self.logger.debug(f"Pattern 4 match: {short_code} {article_number}")

        # Remove duplicates
        unique_citations = []
        seen = set()
        for citation in citations:
            key = (
                citation.get("code_name", ""),
                citation.get("article_number", "")
            )
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)

        self.logger.info(f"Extracted {len(unique_citations)} citations from response")
        return unique_citations

    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text."""
        # Try to find JSON in text
        json_pattern = re.compile(r'\{[^{}]*\}|\{[^{}]*(\{[^{}]*\}[^{}]*)*\}')

        matches = json_pattern.findall(text)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def clean_response(self, text: str) -> str:
        """
        Clean LLM response text - Markdown formatini saqlash!

        ⚠️ MUHIM: Yangi qatorlarni o'chirmaslik!
        """
        # ⭐ FAQAT prefikslarni olib tashlash, yangi qatorlarni saqlash
        prefixes = ["Javob:", "Answer:", "Response:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        # Faqat ortiqcha bo'sh qatorlarni olib tashlash (3+ → 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Bosh va oxiridagi bo'sh joylarni tozalash
        text = text.strip()

        return text