"""
Contractify Backend - FastAPI Modular Monolith

Main application entry point that composes all modules.
Run with: uvicorn app.main:app --reload --port 3000
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import close_db, init_db
from app.core.auth import init_firebase
from app.shared.exceptions import register_exception_handlers

# Import module routers
from app.modules.users import router as users_router
from app.modules.contracts import router as contracts_router
from app.modules.templates import router as templates_router
from app.modules.ai import router as ai_router
from app.modules.documents import router as documents_router
from app.modules.signatures import router as signatures_router
from app.modules.notifications import router as notifications_router
from app.modules.audit import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📝 Debug mode: {settings.debug}")
    print(f"🔗 API prefix: {settings.api_prefix}")

    # Initialize Firebase
    try:
        init_firebase()
        print("🔥 Firebase initialized")
    except Exception as e:
        print(f"⚠️ Firebase not initialized: {e}")

    # Initialize database (create tables if needed)
    try:
        await init_db()
        print("🗄️ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")

    yield

    # Shutdown
    await close_db()
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend for Frontend API for contract generation, signing and management.",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)


# ============== Health Check ==============


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get(f"{settings.api_prefix}/health", tags=["Health"])
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": settings.app_name,
    }


# ============== Include Module Routers ==============
# All routers are included under /api prefix


# Users module - /api/users/*
app.include_router(users_router, prefix=settings.api_prefix)

# Contracts module - /api/contracts/*
app.include_router(contracts_router, prefix=settings.api_prefix)

# Templates module - /api/contracts/templates/*, /api/contracts/types/*
# Note: Templates routes are defined without prefix in the router to match OpenAPI
app.include_router(templates_router, prefix=settings.api_prefix)

# AI module - /api/ai/*
app.include_router(ai_router, prefix=settings.api_prefix)

# Documents module - /api/documents/*
app.include_router(documents_router, prefix=settings.api_prefix)

# Signatures module - /api/signatures/*, /api/contracts/{id}/signatures
app.include_router(signatures_router, prefix=settings.api_prefix)

# Notifications module - /api/notifications/*
app.include_router(notifications_router, prefix=settings.api_prefix)

# Audit module - /api/audit/*
app.include_router(audit_router, prefix=settings.api_prefix)


# ============== Root Endpoint ==============


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": f"{settings.api_prefix}/docs",
        "openapi": f"{settings.api_prefix}/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3000,
        reload=settings.debug,
    )
