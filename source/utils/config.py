"""
Configuration management for BeLagel
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
    app_name: str = "BeLagel"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # OpenAI
    llm_provider: str = "groq"
    groq_api_key: Optional[str] = None
    openai_model: str = "llama-3.3-70b-versatile"
    openai_embedding_model: str = "text-embedding-3-large"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "uzbek_legal_codes"
    qdrant_api_key: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 86400

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/belagel"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

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
            config_path = Path(__file__).parent.parent.parent / "config.yaml"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

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
    if _config_instance is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config_instance


def get_settings() -> Settings:
    """Get settings from environment variables"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

