"""
FastAPI app skeleton for AI BD Lead Assistant (T004+).

Mirrors vanguard-game/backend/app/main.py patterns:
- startup/shutdown for db
- CORS
- health
- include routers (stubs)

Provides:
- GET /api/health
- POST /api/leads/enrich (T007: LLM preview, protected, memory-injected, no CRM token)
- POST /api/leads/push  (auth protected; delegates to T008 lead_service for exact CrmClient flow + T007 enrichment)

T005: basic auth/JWT stub + protected dep.
T007: LLM proxy integrated (Gemini primary + Haiku; enrich before Crm).
T008: orchestration extracted to services/lead_service.py (create_lead_with_followups).
CRM tokens via ?token or settings (demo); create_crm_client called from service.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.leads import router as leads_router
from app.api.connections import router as connections_router
from app.api.memory import router as memory_router
from app.api.usage import router as usage_router

logger = logging.getLogger(__name__)

# ─── T005: Basic auth/JWT stub ───────────────────────────────────────────────
# T010: get_current_user (+ HTTPBearer security dep + placeholder JWT decode)
# was extracted to app.api.leads as get_current_user_api (routes now live there).
# Kept out of this module to avoid dead code; see app/api/leads.py for the
# canonical auth dependency used by all /api/leads/* routes.

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Configure CORS (restricted per review finding; set CORS_ORIGINS env var for dev)
# In production behind nginx reverse proxy, /api requests are same-origin so CORS is not needed.
# For dev frontend (Vite on :5173), set CORS_ORIGINS=http://localhost:5173
import os
_cors_origins_str = os.getenv("CORS_ORIGINS", "") or ""
_cors_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()] if _cors_origins_str else ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting up BD Lead Assistant API...")
    await init_db()
    logger.info("Database initialized (stub models)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    logger.info("Shutting down BD Lead Assistant API...")
    await close_db()
    logger.info("Database connections closed")


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Basic health endpoint."""
    return {"status": "ok", "version": settings.APP_VERSION, "provider_default": settings.DEFAULT_CRM_PROVIDER}


# Include routers from app.api (auth, leads, connections, memory, usage)
app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(connections_router)
app.include_router(memory_router)
app.include_router(usage_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
