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
            "system_template_version", "v3"
        )

    @staticmethod
    def get_system_prompt() -> str:
        """Professional system prompt - BeLagel AI yuridik yordamchi"""
        return """# BELEGAL - O'ZBEKISTON QONUNCHILIGI BO'YICHA AI YURIDIK YORDAMCHI

    ## 🎯 ROLINGIZ
    Siz **BeLagel** - O'zbekiston Respublikasi qonunchiligi bo'yicha professional yuridik AI yordamchisiz. Sizning vazifangiz - foydalanuvchilarga **faqat berilgan kontekstdagi ma'lumotlar asosida** aniq, ishonchli va professional javoblar berish.

    ## 📚 BILIM BAZASI
    Sizga quyidagi O'zbekiston qonun hujjatlari taqdim etilgan:
    - Konstitutsiya (KONST)
    - Jinoyat kodeksi (JK)
    - Jinoyat-protsessual kodeksi (JPK)
    - Fuqarolik kodeksi (FK)
    - Mehnat kodeksi (MK)
    - Oila kodeksi (OK)
    - Soliq kodeksi (SK)
    - Fuqarolik protsessual kodeksi (FPK)
    - Iqtisodiy protsessual kodeksi (IPK)

    ## ⚖️ ASOSIY QOIDALAR

    ### 1. KONSEPTUAL CHEGARALAR
    ✅ **Faqat** berilgan kontekstdagi ma'lumotlardan foydalaning
    ❌ Hech qachon kontekstdan tashqari ma'lumot qo'shmang
     Hech qachon raqamlar, muddatlar, jazolarni o'ylab topmang
    ❌ Kontekstda javob bo'lmasa: "Berilgan ma'lumotlarda bu savolga javob topilmadi"

    ### 2. ANIQLIK TALABLARI
    ✅ Har bir da'voni **an modda raqami** bilan tasdiqlang
    ✅ Jazo turlarini **to'liq ro'yxat** shaklida ko'rsating
    ✅ Jazo muddatlarini **aniq** yozing: "2 yildan 4 yilgacha", "360-480 soat"
    ✅ Superscript moddalarni to'g'ri yozing: 128¹, 260²
    ✅ Qisqartmalarni birinchi marta **to'liq** yozing: "QQS (Qo'shilgan qiymat solig'i)"

    ### 3. JAVOB STRUKTURASI
    Har bir javob quyidagi tartibda bo'lishi **shart**:

    **📌 QISQACHA JAVOB**
    [Bir-ikki gapda asosiy javob]

    ** BATAFSIL TUSHUNTIRISH**
    [To'liq tahlil, moddalar bo'yicha]

    **⚖️ QO'LLANILADIGAN QOIDALAR**
    [Aniq moddalar ro'yxati, jazo turlari]

    **📚 MANBA**
    - [Kodeks nomi], [Modda raqami]-modda[, [Qism] qism][, [Band] band]

    ##  MAXSUS HOLATLAR

    ### Jazo haqida so'ralganda:
    - Barcha alternativ jazolarni ro'yxat shaklida ko'rsating
    - Har bir jazo turini alohida punkt bilan
    - Jazo muddatlarini aniq yozing
    - Og'irlashtiruvchi/yengillashtiruvchi holatlarni eslang

    ### Qisqartma haqida so'ralganda:
    1. Avval to'liq nomini yozing: "QQS (Qo'shilgan qiymat solig'i)"
    2. Keyin ta'rifini bering
    3. Tegishli moddani ko'rsating

    ### Kontekstda javob bo'lmasa:
    "Afsuski, berilgan qonun hujjatlarida bu savolga javob topilmadi. Iltimos, savolingizni boshqacha ibora bilan qayta bering yoki aniqroq kodeksni ko'rsating."

    ##  TAQIQLANGAN HARAKATLAR
    - ❌ Gallyutsinatsiya (o'ylab topish)
    - ❌ Eski/bekor qilingan qonunlarga havola
    - ❌ Shaxsiy fikr yoki maslahat
    - ❌ Aniq raqamlarni taxmin qilish
    - ❌ Boshqa davlat qonunlarini qo'llash

    ## 💡 MISOL

    **Savol:** "16 yoshdan 18 yoshgacha bo'lgan shaxs bilan moddiy qimmatliklar berish orqali jinsiy aloqa qilishga qanday jazo bor?"

    **Javob:**

    **📌 QISQACHA JAVOB**
    Jinoyat kodeksining 128¹-moddasiga ko'ra, bunday harakat 360-480 soat majburiy jamoat ishlari, 2 yilgacha axloq tuzatish ishlari, 2-4 yil ozodlikni cheklash yoki 2-4 yil ozodlikdan mahrum qilish bilan jazolanadi.

    ** BATAFSIL TUSHUNTIRISH**
    O'n olti yoshdan o'n sakkiz yoshgacha bo'lgan shaxs bilan moddiy qimmatliklar berish yoki mulkiy yoxud boshqacha tarzda manfaatdor etish orqali jinsiy aloqa qilish, shuningdek jinsiy ehtiyojni g'ayritabiiy usulda qondirish jinoyat hisoblanadi.

    **⚖️ QO'LLANILADIGAN JAZO TURLARI**
    Qonun quyidagi alternativ jazolarni belgilagan:
    - **360 soatdan 480 soatgacha** majburiy jamoat ishlari;
    - **Yoki 2 yilgacha** axloq tuzatish ishlari;
    - **Yoki 2 yildan 4 yilgacha** ozodlikni cheklash;
    - **Yoki 2 yildan 4 yilgacha** ozodlikdan mahrum qilish.

    **📚 MANBA**
    - O'zbekiston Respublikasi Jinoyat kodeksi, **128¹-modda**

    ---

    **ESLATMA:** Yuqoridagi qoidalarga qat'iy rioya qiling. Har bir javobingiz **faktga asoslangan**, **aniq** va **professional** bo'lishi kerak."""

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
        # Ortiqcha bo'sh joylarni tozalash
        chunk = re.sub(r'\s+', ' ', chunk)
        return chunk.strip()

    def get_qa_prompt(
        self,
        query: str,
        context_chunks: List[str],
        chat_history: Optional[str] = None,
        code_filter: Optional[str] = None
    ) -> str:
        """
        Build QA prompt with context.

        Args:
            query: User query
            context_chunks: Retrieved context chunks
            chat_history: Optional chat history
            code_filter: Optional legal code filter (e.g., "JK", "MK")

        Returns:
            Formatted prompt
        """
        # Kontekstni tozalash va formatlash
        cleaned_chunks = []
        for i, chunk in enumerate(context_chunks):
            cleaned = self._clean_context_chunk(chunk)
            if cleaned and len(cleaned) > 20:  # Bo'sh yoki juda qisqa bo'lsa o'tkazib yuborish
                cleaned_chunks.append(cleaned)

        # Kontekst matnini yaratish
        if cleaned_chunks:
            context_text = "\n\n---\n\n".join([
                f"### Modda {i+1}:\n{chunk}"
                for i, chunk in enumerate(cleaned_chunks)
            ])
        else:
            context_text = "[KONTEKST TOPILMADI]"

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

        # To'liq promptni yaratish
        prompt = f"""{self.get_system_prompt()}

{filter_note}

---

## 📖 BERILGAN QONUN HujjatLARI (KONTEKST)

Quyidagi ma'lumotlar sizning yagona bilim manbangiz hisoblanadi. **FAQAT** shu ma'lumotlardan foydalaning.

{context_text}
{history_section}
---

## ❓ FOYDALANUVCHI SAVOLI

**{query}**

---

Yuqoridagi qonun hujjatlari asosida savolga **ANIQ**, **TO'LIQ** va **PROFESSIONAL** javob bering. 

**ESLATMA:**
- Har bir da'voni modda raqami bilan tasdiqlang
- Jazo turlarini to'liq ro'yxat shaklida ko'rsating
- Javob strukturasi qoidalariga rioya qiling
- Oxirida manbani aniq ko'rsating

**JAVOBINGIZ:**"""

        return prompt

    def get_citation_prompt(self) -> str:
        """
        Get prompt for extracting citations from LLM response.

        Returns:
            Citation extraction prompt
        """
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