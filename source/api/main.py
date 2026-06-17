# source/api/main.py
"""
BeLagel - O'zbekiston Qonunchiligi uchun AI Q&A Tizimi
FastAPI Application Entry Point
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Loyiha ildizini PATH ga qo'shish
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from source.api.routes import router
from source.utils.config import get_settings, load_config  # <-- load_config QO'SHILDI!
from source.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Ilova ishga tushganda va to'xtaganda bajariladigan amallar
    """
    # ⭐ ENG MUHIM: Config ni yuklash!
    load_config()  # <-- BU QATOR QO'SHILDI!

    # STARTUP
    logger.info("=" * 60)
    logger.info("🚀 BeLagel API ishga tushmoqda...")
    logger.info("=" * 60)

    settings = get_settings()
    logger.info(f"📝 Ilova: {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Muhit: {settings.environment}")

    # RAG Service ni ishga tushirish
    try:
        from source.services.rag_service import RAGService
        rag_service = RAGService()
        await rag_service.initialize()
        app.state.rag_service = rag_service
        logger.info("✅ RAG Service muvaffaqiyatli ishga tushdi")
    except Exception as e:
        logger.error(f"❌ RAG Service ishga tushishda xato: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("✅ BeLagel API tayyor!")
    logger.info("=" * 60)

    yield

    # SHUTDOWN
    logger.info("🛑 BeLagel API to'xtatilmoqda...")
    if hasattr(app.state, 'rag_service'):
        await app.state.rag_service.shutdown()
    logger.info("✅ BeLagel API to'xtatildi")


def create_app() -> FastAPI:
    """
    FastAPI ilovasini yaratish va sozlash
    """
    # Config ni yuklash
    load_config()

    settings = get_settings()

    # Logging ni sozlash
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file
    )

    # FastAPI ilovasini yaratish
    application = FastAPI(
        title=settings.app_name,
        description="O'zbekiston qonunchiligi bo'yicha AI yordamchi",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip compression
    application.add_middleware(GZipMiddleware, minimum_size=1000)

    # Routes ni qo'shish
    application.include_router(router, prefix="/api/v1")

    # Root endpoint
    @application.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled"
        }

    # Health check
    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.app_version
        }

    return application


# ⭐ MUHIM: app o'zgaruvchisini yaratish!
app = create_app()

# Agar to'g'ridan-to'g'ri python main.py bilan ishga tushirilsa
if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "source.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )