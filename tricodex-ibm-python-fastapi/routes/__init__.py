"""
API routes and dependencies for ProcessLens
"""
from fastapi import APIRouter
from routes.analysis import router as analysis_router
from routes.health import router as health_router
from routes.websocket import router as ws_router

# Create main router
api_router = APIRouter()

# Include sub-routers with consistent paths
api_router.include_router(analysis_router, prefix="/analyze", tags=["analysis"])  # Changed from /analysis to /analyze
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(ws_router, prefix="/ws", tags=["websocket"])

__all__ = ["api_router"]