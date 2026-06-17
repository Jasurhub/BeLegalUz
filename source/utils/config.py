"""
Configuration management for BeLagel
Vercel va lokal muhit uchun moslashtirilgan
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="BeLagel", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")

    # LLM Provider
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")

    # Groq
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # OpenAI (agar kerak bo'lsa)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-large", alias="OPENAI_EMBEDDING_MODEL")

    # LLM Settings
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")

    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection_name: str = Field(default="uzbek_legal_codes", alias="QDRANT_COLLECTION_NAME")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    cache_ttl: int = Field(default=86400, alias="CACHE_TTL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/belagel",
        alias="DATABASE_URL"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", alias="LOG_FILE")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, alias="RATE_LIMIT_WINDOW")

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000,https://belagel-frontend.vercel.app",
        alias="ALLOWED_ORIGINS"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


class Config:
    """YAML configuration loader"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file
        """
        if config_path is None:
            # Vercel va lokal uchun moslashuvchan path
            config_path = Path(__file__).parent.parent.parent / "config.yaml"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            # Vercel'da config.yaml bo'lmasligi mumkin, default qiymatlarni ishlatamiz
            self._config = self._get_default_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for Vercel"""
        return {
            "chunking": {
                "strategy": "article_level",
                "max_chunk_size": 1500,
                "chunk_overlap": 200
            },
            "embedding": {
                "model": "intfloat/multilingual-e5-large",
                "dimension": 1024,
                "batch_size": 32
            },
            "vectordb": {
                "provider": "qdrant",
                "url": "http://localhost:6333",
                "collection_name": "uzbek_legal_codes",
                "distance": "cosine"
            },
            "retrieval": {
                "top_k": 5,
                "score_threshold": 0.5,
                "use_reranker": False
            },
            "legal_codes": [
                {"name": "O'zbekiston Respublikasi Konstitutsiyasi", "short_code": "KONST", "file_pattern": "KONSTITUTSIYASI"},
                {"name": "O'zbekiston Respublikasi Jinoyat kodeksi", "short_code": "JK", "file_pattern": "JINOYAT KODEKSI"},
                {"name": "O'zbekiston Respublikasi Jinoyat-protsessual kodeksi", "short_code": "JPK", "file_pattern": "JINOYAT-PROTSESSUAL"},
                {"name": "O'zbekiston Respublikasi Fuqarolik kodeksi", "short_code": "FK", "file_pattern": "FUQAROLIK KODEKSI"},
                {"name": "O'zbekiston Respublikasi Mehnat kodeksi", "short_code": "MK", "file_pattern": "Mehnat kodeksi"},
                {"name": "O'zbekiston Respublikasi Oila kodeksi", "short_code": "OK", "file_pattern": "OILA KODEKSI"},
                {"name": "O'zbekiston Respublikasi Soliq kodeksi", "short_code": "SK", "file_pattern": "Soliq kodeksi"},
                {"name": "O'zbekiston Respublikasi Fuqarolik protsessual kodeksi", "short_code": "FPK", "file_pattern": "Fuqarolik protsessual"},
                {"name": "O'zbekiston Respublikasi Iqtisodiy protsessual kodeksi", "short_code": "IPK", "file_pattern": "Iqtisodiy protsessual"},
                {"name": "O'zbekiston Respublikasi Ma'muriy javobgarlik to'g'risidagi kodeksi", "short_code": "MJK", "file_pattern": "Ma'muriy javobgarlik"}
            ],
            "llm": {
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "prompt": {
                "system_template_version": "v3"
            },
            "cache": {
                "enabled": True,
                "ttl": 86400
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., "chunking.strategy")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def chunking(self) -> Dict[str, Any]:
        """Get chunking configuration"""
        return self._config.get("chunking", {})

    @property
    def embedding(self) -> Dict[str, Any]:
        """Get embedding configuration"""
        return self._config.get("embedding", {})

    @property
    def vectordb(self) -> Dict[str, Any]:
        """Get vector database configuration"""
        return self._config.get("vectordb", {})

    @property
    def retrieval(self) -> Dict[str, Any]:
        """Get retrieval configuration"""
        return self._config.get("retrieval", {})

    @property
    def legal_codes(self) -> List[Dict[str, str]]:
        """Get legal codes configuration"""
        return self._config.get("legal_codes", [])

    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config.get("llm", {})

    @property
    def prompt(self) -> Dict[str, Any]:
        """Get prompt configuration"""
        return self._config.get("prompt", {})

    @property
    def cache(self) -> Dict[str, Any]:
        """Get cache configuration"""
        return self._config.get("cache", {})


# Global configuration instance
_config_instance: Optional[Config] = None
_settings_instance: Optional[Settings] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load and return configuration.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def get_config() -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        # Avtomatik yuklash
        _config_instance = Config()
    return _config_instance


def get_settings() -> Settings:
    """Get settings from environment variables"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance