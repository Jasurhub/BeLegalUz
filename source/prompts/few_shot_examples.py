"""
Few-shot examples for legal Q&A
"""

from typing import List, Dict

class FewShotExamples:
    """
    Provides few-shot examples for better LLM performance.
    """
    
    @staticmethod
    def get_legal_qa_examples() -> List[Dict[str, str]]:
        """
        Get few-shot examples for legal Q&A.
        
        Returns:
            List of example dictionaries
        """
        return [
            {
                "query": "Mehnat ta'tili necha kun?",
                "context": "Mehnat kodeksi 139-modda: Asosiy mehnat ta'tili kamida 15 kalendar kunidan iborat bo'ladi.",
                "answer": "O'zbekiston Respublikasi Mehnat kodeksining 139-moddasiga ko'ra, asosiy mehnat ta'tili kamida 15 kalendar kunidan iborat.\n\nManba: O'zbekiston Respublikasi Mehnat kodeksi, 139-modda"
            },
            {
                "query": "Jinoyat uchun qanday jazolar bor?",
                "context": "Jinoyat kodeksi 43-modda: Jinoyat uchun quyidagi jazolar qo'llanilishi mumkin: jarima, axloq tuzatish ishlari, qamoq, ozodlikdan mahrum qilish.",
                "answer": "Jinoyat kodeksining 43-moddasiga ko'ra, jinoyat uchun quyidagi jazolar qo'llanilishi mumkin:\n1. Jarima\n2. Axloq tuzatish ishlari\n3. Qamoq\n4. Ozodlikdan mahrum qilish\n\nManba: O'zbekiston Respublikasi Jinoyat kodeksi, 43-modda"
            },
            {
                "query": "Soliq deklaratsiyasi qachon topshiriladi?",
                "context": "Soliq kodeksi 320-modda: Jismoniy shaxslar daromad solig'i deklaratsiyasini har yili 1 apreldan kechiktirmay topshiradilar.",
                "answer": "Soliq kodeksining 320-moddasiga ko'ra, jismoniy shaxslar daromad solig'i deklaratsiyasini har yili 1 apreldan kechiktirmay topshirishlari kerak.\n\nManba: O'zbekiston Respublikasi Soliq kodeksi, 320-modda"
            }
        ]
    
    @staticmethod
    def get_citation_examples() -> List[Dict]:
        """
        Get examples for citation extraction.
        
        Returns:
            List of citation examples
        """
        return [
            {
                "text": "Mehnat kodeksining 100-moddasiga ko'ra, ish beruvchi xodimni ishdan bo'shatishi mumkin.",
                "citations": [
                    {"code_name": "O'zbekiston Respublikasi Mehnat kodeksi", "article_number": "100"}
                ]
            },
            {
                "text": "JK 125-modda va JPK 230-moddaga muvofiq, ushbu holatda javobgarlik belgilangan.",
                "citations": [
                    {"code_name": "O'zbekiston Respublikasi Jinoyat kodeksi", "article_number": "125"},
                    {"code_name": "O'zbekiston Respublikasi Jinoyat-protsessual kodeksi", "article_number": "230"}
                ]
            }
        ]