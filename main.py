"""
Main entry point for BeLagel application
"""
import sys
from pathlib import Path

# Loyiha ildizini PATH ga qo'shish
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from source.utils.config import get_settings
from source.utils.logger import setup_logging


def main():
    """Run the application"""
    # Load settings
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file
    )
    
    # Run uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers if settings.environment == "production" else 1,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()