"""
Main FastAPI application entry point.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import create_tables
from .routers import quiz

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan management.
    """
    # Startup
    logger.info("Starting up Quiz Generator API...")

    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")

    # Test Gemini API connection
    try:
        from .services.gemini_service import gemini_service

        is_connected = await gemini_service.test_api_connection()
        if is_connected:
            logger.info("Gemini API connection successful")
        else:
            logger.warning("Gemini API connection test failed")
    except Exception as e:
        logger.error(f"Error testing Gemini API connection: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Quiz Generator API...")


# Create FastAPI application
app = FastAPI(
    title="Quiz Generator API",
    description="AI-powered quiz generation using Google Gemini API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quiz.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Quiz Generator API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "quiz-generator-api", "version": "1.0.0"}


@app.get("/api/v1/health")
async def api_health_check() -> dict[str, str]:
    """API-specific health check with Gemini connection test."""
    try:
        from .services.gemini_service import gemini_service

        gemini_status = await gemini_service.test_api_connection()
    except Exception as e:
        logger.error(f"Gemini API health check failed: {e}")
        gemini_status = False

    return {
        "status": "healthy",
        "database": "connected",
        "gemini_api": "connected" if gemini_status else "disconnected",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
