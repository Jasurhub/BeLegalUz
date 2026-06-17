# BeLagel API Dokumentatsiyasi

BeLagel REST API O'zbekiston qonunchiligi bo'yicha savollarga javob berish uchun mo'ljallangan.

## Asosiy Ma'lumotlar
- **Base URL:** `http://localhost:8000/api/v1`
- **Content-Type:** `application/json`
- **Autentifikatsiya:** Hozircha ochiq (Production da API Key qo'shiladi)

---

## Endpoint'lar

### 1. Health Check
Tizim holatini tekshirish.

**GET** `/health`

**Javob (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "api": true,
    "database": true,
    "llm": true
  }
}