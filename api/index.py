# api/index.py
"""
Vercel Serverless Function Entry Point
"""
import sys
from pathlib import Path

# Loyiha ildizini PATH ga qo'shish
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config yuklash
from source.utils.config import load_config, get_settings
load_config()

# FastAPI app yaratish
from source.api.main import app as fastapi_app
app = fastapi_app

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "platform": "vercel",
        "service": "BeLagel Backend",
        "llm_provider": settings.llm_provider,
        "qdrant_url": settings.qdrant_url[:50] + "..."
    }

# Vercel handler
handler = app