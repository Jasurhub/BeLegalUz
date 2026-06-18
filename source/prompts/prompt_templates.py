"""
Prompt templates for legal Q&A - Professional Version
BeLagel - O'zbekiston Qonunchiligi uchun AI Q&A Tizimi
"""

from typing import List, Optional, Dict, Any
import re
from source.utils.config import get_config


class PromptTemplates:
    """
    Manages prompt templates for legal Q&A system.
    Professional yuridik javoblar uchun optimallashtirilgan.
    """

    def __init__(self):
        """Initialize prompt templates"""
        self.config = get_config()
        self.version = self.config.prompt.get(
            "system_template_version", "v4"  # ← v3 dan v4 ga o'zgartirildi
        )

    @staticmethod
    def get_system_prompt() -> str:
        """Professional system prompt - BeLagel AI yuridik yordamchi"""
        return """# BELEGAL - O'ZBEKISTON QONUNCHILIGI BO'YICHA AI YURIDIK YORDAMCHI

## 🎯 ROLINGIZ
Siz **BeLagel** - O'zbekiston Respublikasi qonunchiligi bo'yicha professional yuridik AI yordamchisiz. Sizning vazifangiz - foydalanuvchilarga **faqat berilgan kontekstdagi ma'lumotlar asosida** aniq, ishonchli va professional javoblar berish.

## ⚖️ ASOSIY QOIDALAR (BUZILMAS!)

### 1. FAKTGA ASOSLANGANLIK - ENG MUHIM!
✅ **Faqat** berilgan kontekstdagi ma'lumotlardan foydalaning
❌ Hech qachon kontekstdan tashqari ma'lumot QO'SHMANG
❌ Hech qachon modda raqamlarini O'YLAb TOPMANG
❌ Kontekstda yo'q modda raqamlarini yozmang
❌ Kontekstda javob bo'lmasa: "Berilgan ma'lumotlarda bu savolga javob topilmadi"

### 2. MODDA RAQAMLARI - ANIQ BO'LSIN!
✅ Har bir da'voni kontekstdagi ANIQ modda raqami bilan tasdiqlang
✅ Modda raqamlarini kontekstdan OLING (masalan: "163-modda", "164-modda")
❌ "Modda 1", "Modda 2", "Modda 4", "Modda 5" kabi umumiy raqamlarni ishlatmang
❌ Kontekstda ko'rsatilmagan modda raqamlarini yozmang

### 3. ANIQLIK TALABLARI
✅ Jazo turlarini **to'liq ro'yxat** shaklida ko'rsating
✅ Jazo muddatlarini **aniq** yozing: "2 yildan 4 yilgacha", "360-480 soat"
✅ Superscript moddalarni to'g'ri yozing: 128¹, 260²
✅ Qisqartmalarni birinchi marta **to'liq** yozing: "QQS (Qo'shilgan qiymat solig'i)"

### 4. JAVOB STRUKTURASI
Har bir javob quyidagi tartibda bo'lishi **shart**:

### 📌 QISQACHA JAVOB
[Bir-ikki gapda asosiy javob]

### 📖 BATAFSIL TUSHUNTIRISH
[To'liq tahlil, moddalar bo'yicha]

### ⚖️ QO'LLANILADIGAN QOIDALAR
[Aniq moddalar ro'yxati, jazo turlari]

### 📚 MANBA
- [Kodeksning to'liq nomi], **[Modda raqami]-modda**

## 🚫 TAQIQLANGAN HARAKATLAR
- ❌ Gallyutsinatsiya (o'ylab topish)
- ❌ Kontekstda yo'q modda raqamlarini yozish
- ❌ Umumiy modda raqamlarini ishlatish ("Modda 1", "Modda 2")
- ❌ Eski/bekor qilingan qonunlarga havola
- ❌ Shaxsiy fikr yoki maslahat
- ❌ Boshqa davlat qonunlarini qo'llash

## 💡 MISOL (TO'G'RI JAVOB)

**Savol:** "Korxona soliq organining qaroridan norozi bo'lsa qayerga murojaat qiladi?"

**Kontekstda:**
- 163-modda: Shikoyat qilinganda soliq organlari qarorlarini ijro etish...
- 164-modda: Soliq organlarining qarorlarini ijro etish...

**To'g'ri Javob:**

### 📌 QISQACHA JAVOB
Korxona soliq organining qaroridan norozi bo'lsa, yuqori turuvchi soliq organiga shikoyat qiladi.

### 📖 BATAFSIL TUSHUNTIRISH
Soliq kodeksining **163-moddasiga** ko'ra, soliq tekshiruvi natijalari bo'yicha qabul qilingan soliq organining qarori ustidan shikoyat qilinganda, bunday qaror yuqori turuvchi soliq organi tomonidan bekor qilinmagan va ustidan shikoyat qilinmagan qismi bo'yicha shikoyat yuzasidan yuqori turuvchi soliq organi tomonidan qaror qabul qilingan kundan e'tiboran kuchga kiradi.

**164-moddaga** ko'ra, soliq tekshiruvi natijalari bo'yicha qaror u kuchga kirgan kundan e'tiboran ijro etilishi lozim.

### ⚖️ QO'LLANILADIGAN QOIDALAR
- Soliq organining qarori ustidan shikoyat qilish tartibi **163-modda** da belgilangan
- Qarorni ijro etish tartibi **164-modda** da belgilangan

### 📚 MANBA
- O'zbekiston Respublikasi Soliq kodeksi, **163-modda**
- O'zbekiston Respublikasi Soliq kodeksi, **164-modda**

---

**ESLATMA:** Har bir javobingiz **faktga asoslangan**, **aniq modda raqamlari** bilan bo'lishi kerak!"""

    def _clean_context_chunk(self, chunk: str) -> str:
        """Kontekst chunkini tozalash - HTML teglarini olib tashlash"""
        # HTML teglarini olib tashlash
        chunk = re.sub(r'<[^>]+>', ' ', chunk)
        # HTML entity'larni tozalash
        chunk = chunk.replace('&nbsp;', ' ')
        chunk = chunk.replace('&amp;', '&')
        chunk = chunk.replace('&lt;', '<')
        chunk = chunk.replace('&gt;', '>')
        # URL'larni olib tashlash
        chunk = re.sub(r'https?://\S+', '', chunk)
        # Ortiqcha bo'sh joylarni tozalash (lekin yangi qatorlarni saqlash)
        chunk = re.sub(r'[ \t]+', ' ', chunk)  # ← Faqat gorizontal bo'sh joylar
        return chunk.strip()

    def get_qa_prompt(
        self,
        query: str,
        context_chunks: List[str],
        chat_history: Optional[str] = None,
        code_filter: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None  # ← YANGI PARAMETR
    ) -> str:
        """
        Build QA prompt with context.

        Args:
            query: User query
            context_chunks: Retrieved context chunks
            chat_history: Optional chat history
            code_filter: Optional legal code filter (e.g., "JK", "MK")
            sources: List of source metadata (code_name, article_number)
        """
        # ⭐ MUHIM: Kontekstni manbalar bilan birga formatlash
        context_text = self._format_context_with_sources(context_chunks, sources)

        # Code filter haqida eslatma
        filter_note = ""
        if code_filter and code_filter != "null" and code_filter.strip():
            filter_note = f"""
⚠️ **MUHIM ESLATMA:** Foydalanuvchi faqat **{code_filter}** kodeksi bo'yicha javob so'ramoqda.
Boshqa kodekslarga murojaat QILMANG. Faqat {code_filter} kodeksidagi moddalardan foydalaning.
"""

        # Suhbat tarixi
        history_section = ""
        if chat_history:
            history_section = f"""
## 💬 SUHBAT TARIXI
{chat_history}
"""

        # ⭐ MUHIM: Mavjud modda raqamlarini aniq ko'rsatish
        available_articles = ""
        if sources:
            article_list = [f"{s.get('article_number', '?')}-modda" for s in sources if s.get('article_number')]
            if article_list:
                available_articles = f"""
📋 **KONTEKSTDA MAVJUD MODDALAR:** {', '.join(article_list)}
⚠️ **Faqat shu modda raqamlaridan foydalaning! Boshqa modda raqamlarini O'YLAb TOPMANG!**
"""

        # To'liq promptni yaratish
        prompt = f"""{self.get_system_prompt()}

{filter_note}
{available_articles}

---

## 📖 BERILGAN QONUN HujjatLARI (KONTEKST)

Quyidagi ma'lumotlar sizning yagona bilim manbangiz hisoblanadi. **FAQAT** shu ma'lumotlardan foydalaning.

{context_text}
{history_section}
---

## ❓ FOYDALANUVCHI SAVOLI

**{query}**

---

## 📝 JAVOB BERISH QOIDALARI

1. **Faqat yuqoridagi kontekstdan foydalaning**
2. **Aniq modda raqamlarini ko'rsating** (masalan: "163-modda", "164-modda")
3. **"Modda 1", "Modda 2" kabi umumiy raqamlarni ishlatmang**
4. **Markdown formatida yozing** (##, **, -)
5. **Oxirida manbani aniq ko'rsating**

**JAVOBINGIZ:**"""

        return prompt

    def _format_context_with_sources(
        self,
        context_chunks: List[str],
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Kontekstni manbalar bilan birga formatlash.
        Har bir chunk uchun modda raqamini aniq ko'rsatish.
        """
        if not context_chunks:
            return "[KONTEKST TOPILMADI]"

        formatted_parts = []

        for i, chunk in enumerate(context_chunks):
            cleaned = self._clean_context_chunk(chunk)
            if not cleaned or len(cleaned) < 20:
                continue

            # Manba ma'lumotini olish
            source_info = ""
            if sources and i < len(sources):
                source = sources[i]
                code_name = source.get('code_name', '')
                article_number = source.get('article_number', '')
                code_short = source.get('code_short', '')

                if article_number:
                    source_info = f"\n📌 **MANBA: {code_name}, {article_number}-modda** ({code_short})\n"

            formatted_parts.append(
                f"### KONTEKST {i+1}:{source_info}\n{cleaned}"
            )

        return "\n\n---\n\n".join(formatted_parts)

    def get_citation_prompt(self) -> str:
        """Get prompt for extracting citations from LLM response."""
        return """Quyidagi javobdan barcha yuridik manbalarni (kodeks nomi va modda raqami) ajratib oling.

**QOIDALAR:**
1. Kodeks nomini TO'LIQ yozing (masalan: "O'zbekiston Respublikasi Jinoyat kodeksi")
2. Modda raqamini aniq ko'rsating (shu jumladan superscript: 128¹, 260²)
3. Qism yoki band raqami bo'lsa, uni ham qo'shing

**FORMAT:**
```json
{
  "citations": [
    {"code_name": "O'zbekiston Respublikasi Jinoyat kodeksi", "article_number": "128¹", "part": "1"},
    {"code_name": "O'zbekiston Respublikasi Mehnat kodeksi", "article_number": "136"}
  ]
}"""