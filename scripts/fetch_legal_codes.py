#!/usr/bin/env python3
"""
Automatic fetcher for Uzbekistan legal codes from lex.uz
"""

import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup
import re
from source.utils.logger import setup_logging, get_logger
from source.utils.config import load_config

logger = get_logger(__name__)

# Legal codes URLs on lex.uz
LEGAL_CODES_URLS = {
    "konstitutsiya": {
        "name": "O'zbekiston Respublikasi Konstitutsiyasi",
        "short_code": "KONST",
        "url": "https://lex.uz/docs/-16334"
    },
    "jinoyat_kodeksi": {
        "name": "O'zbekiston Respublikasi Jinoyat kodeksi",
        "short_code": "JK",
        "url": "https://lex.uz/docs/-111134"
    },
    "mamuriy_javobgarlik": {
        "name": "O'zbekiston Respublikasi Ma'muriy javobgarlik to'g'risidagi kodeksi",
        "short_code": "MJK",
        "url": "https://lex.uz/docs/-111454"
    },
    "fuqarolik_kodeksi": {
        "name": "O'zbekiston Respublikasi Fuqarolik kodeksi",
        "short_code": "FK",
        "url": "https://lex.uz/docs/-111262"
    },
    "mehnat_kodeksi": {
        "name": "O'zbekiston Respublikasi Mehnat kodeksi",
        "short_code": "MK",
        "url": "https://lex.uz/docs/-111386"
    },
    "oila_kodeksi": {
        "name": "O'zbekiston Respublikasi Oila kodeksi",
        "short_code": "OK",
        "url": "https://lex.uz/docs/-111445"
    },
    "soliq_kodeksi": {
        "name": "O'zbekiston Respublikasi Soliq kodeksi",
        "short_code": "SK",
        "url": "https://lex.uz/docs/-111442"
    },
    "jinoyat_protsessual": {
        "name": "O'zbekiston Respublikasi Jinoyat-protsessual kodeksi",
        "short_code": "JPK",
        "url": "https://lex.uz/docs/-111135"
    },
    "fuqarolik_protsessual": {
        "name": "O'zbekiston Respublikasi Fuqarolik protsessual kodeksi",
        "short_code": "FPK",
        "url": "https://lex.uz/docs/-111263"
    },
    "iqtisodiy_protsessual": {
        "name": "O'zbekiston Respublikasi Iqtisodiy protsessual kodeksi",
        "short_code": "IPK",
        "url": "https://lex.uz/docs/-111520"
    }
}


class LegalCodeFetcher:
    """Fetcher for legal codes from lex.uz"""

    def __init__(self, output_dir: str = "./data/codes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.logger = logger

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_code(self, code_key: str, code_info: Dict) -> bool:
        """
        Fetch a single legal code.

        Args:
            code_key: Code identifier
            code_info: Code information dict

        Returns:
            True if successful
        """
        url = code_info["url"]
        name = code_info["name"]

        try:
            self.logger.info(f"Fetching {name} from {url}")

            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to fetch {name}: HTTP {response.status}")
                    return False

                html = await response.text(encoding='utf-8')

                # Parse HTML
                content = self._parse_lex_uz_html(html)

                if not content:
                    self.logger.warning(f"No content extracted for {name}")
                    return False

                # Save to file
                filename = f"{code_key}.html"
                filepath = self.output_dir / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.logger.info(f"✓ Saved {name} to {filepath}")
                return True

        except Exception as e:
            self.logger.error(f"Error fetching {name}: {str(e)}")
            return False

    def _parse_lex_uz_html(self, html: str) -> str:
        """
        Parse lex.uz HTML and extract legal text.

        Args:
            html: Raw HTML

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'lxml')

        # Try to find main content area
        # lex.uz structure may vary, try multiple selectors
        content_selectors = [
            "div.document-content",
            "div.content",
            "div#content",
            "article",
            "div.text"
        ]

        content_div = None
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break

        if not content_div:
            # Fallback: get entire body
            content_div = soup.body if soup.body else soup

        # Remove scripts and styles
        for element in content_div(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text
        text = content_div.get_text(separator='\n', strip=True)

        # Clean up text
        text = self._clean_text(text)

        return text

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # Remove extra spaces
        text = re.sub(r' +', ' ', text)

        # Remove special characters that might cause issues
        text = re.sub(r'[^\S\n]+', ' ', text)

        return text.strip()

    async def fetch_all_codes(self) -> Dict[str, bool]:
        """
        Fetch all legal codes.

        Returns:
            Dictionary of results
        """
        results = {}

        # Fetch sequentially to avoid overwhelming the server
        for code_key, code_info in LEGAL_CODES_URLS.items():
            success = await self.fetch_code(code_key, code_info)
            results[code_key] = success

            # Be polite - add delay between requests
            await asyncio.sleep(2)

        return results


async def main():
    """Main entry point"""
    setup_logging(log_level="INFO")
    load_config()

    logger.info("=" * 60)
    logger.info("O'zbekiston Qonun Kodekslarini Yuklab Olish")
    logger.info("=" * 60)

    fetcher = LegalCodeFetcher(output_dir="./data/codes")

    async with fetcher:
        results = await fetcher.fetch_all_codes()

    # Summary
    successful = sum(1 for v in results.values() if v)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"Yuklash yakunlandi: {successful}/{total} muvaffaqiyatli")
    logger.info("=" * 60)

    if successful == total:
        logger.info("✅ Barcha kodekslar muvaffaqiyatli yuklandi!")
        logger.info(f"📁 Papka: ./data/codes")
        logger.info("\nEndi quyidagi buyruqni bajaring:")
        logger.info("  python scripts/ingest_data.py --data-dir ./data/codes")
    else:
        logger.warning("⚠️  Ba'zi kodekslarni yuklashda xatolik yuz berdi")
        for code_key, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {code_key}")


if __name__ == "__main__":
    asyncio.run(main())