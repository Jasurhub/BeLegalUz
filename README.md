# BeLagel - O'zbekiston Qonunchiligi uchun AI Q&A Tizimi

Professional RAG (Retrieval-Augmented Generation) tizimi O'zbekiston qonunlari bo'yicha savollarga javob berish uchun.

## Xususiyatlar

- ✅ 10 ta asosiy qonun kodeksi
- ✅ Aniq modda ko'rsatmalari bilan javoblar
- ✅ Gallyutsinatsiyasiz (uydirmasiz) javoblar
- ✅ Tezkor qidiruv va keshlash
- ✅ Professional API va dokumentatsiya

## O'rnatish

### Talablar

- Python 3.11+
- Docker va Docker Compose
- OpenAI API kaliti

### Tez boshlash

```bash
# 1. Loyihani klonlash
git clone <repository-url>
cd uzbek-legal-rag

# 2. Muhitni sozlash
cp .env.example .env
# .env faylini tahrirlang va OPENAI_API_KEY ni kiriting

# 3. Docker orqali ishga tushirish
docker-compose up -d

# 4. Ma'lumotlarni yuklash
python scripts/ingest_data.py --data-dir ./data/codes

# 5. API ga kirish
# http://localhost:8000/docs