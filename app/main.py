"""FastAPI application entry point."""

import os
import sys

# Set Fontconfig config file on Windows before any library (e.g. WeasyPrint) loads it.
# Avoids: "Fontconfig error: Cannot load default config file: No such file: (null)"
if sys.platform == "win32":
    _base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _fonts_conf = os.path.join(_base_dir, "fonts", "fonts.conf")
    if os.path.isfile(_fonts_conf):
        os.environ["FONTCONFIG_FILE"] = _fonts_conf
        _cache_dir = os.path.join(_base_dir, "fonts", "fontconfig-cache")
        os.makedirs(_cache_dir, exist_ok=True)

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import mongodb
from app.core.logging import setup_logging
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routers import auth, company, customers, documents, pdf, products
from app.stats.stats_router import router as stats_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Centralized exception handlers
register_exception_handlers(app)

# Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded logos and PDFs
app.mount("/static", StaticFiles(directory=str(settings.UPLOAD_DIR.parent)), name="static")

# API versioned prefix
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(company.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(pdf.router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB and create indexes on application startup."""
    await mongodb.connect()
    await mongodb.create_indexes()
    logger.info("Application started — %s v%s", settings.APP_TITLE, settings.APP_VERSION)


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully close the MongoDB connection on shutdown."""
    await mongodb.disconnect()
    logger.info("Application shut down")


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}
