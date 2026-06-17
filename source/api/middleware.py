"""
Custom middleware for the API
"""

import time
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from source.utils.logger import get_logger
from source.utils.config import get_settings

logger = get_logger(__name__)


def setup_cors_middleware(app, settings) -> None:
    """
    Setup CORS middleware.
    
    Args:
        app: FastAPI application
        settings: Application settings
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def timing_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    Middleware to log request timing.
    
    Args:
        request: HTTP request
        call_next: Next middleware/handler
    
    Returns:
        Response
    """
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"{request.method} {request.url.path} - {process_time:.3f}s"
    )
    
    return response


async def error_handling_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    Middleware for global error handling.
    
    Args:
        request: HTTP request
        call_next: Next middleware/handler
    
    Returns:
        Response
    """
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        raise