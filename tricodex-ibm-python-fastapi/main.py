"""
ProcessLens FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from db import Database
from routes import api_router
from components.agents.factory import AgentFactory
from config import Config
from utils.logging_config import setup_logging

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        # Startup
        logger.info("Initializing ProcessLens...")
        await Database.connect_db()
        
        # Initialize agents with proper error handling
        try:
            # Create instances first
            watson_agent = AgentFactory.create_agent("watson")
            gemini_agent = AgentFactory.create_agent("gemini")
            function_agent = AgentFactory.create_agent("function")
            
            # Verify initialization
            if not watson_agent or not gemini_agent or not function_agent:
                raise RuntimeError("Failed to initialize one or more agents")
                
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}", exc_info=True)
            raise
        
        logger.info("ProcessLens initialized successfully")
        yield
        
    finally:
        # Cleanup
        logger.info("Shutting down ProcessLens...")
        await Database.close_db()
        AgentFactory.reset_agents()
        logger.info("Cleanup complete")

# Initialize FastAPI application
app = FastAPI(
    title="ProcessLens API",
    description="Process Mining and Analysis with IBM Granite",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.update({
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    })
    return response

# Include API routers
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    """API root information"""
    return {
        "name": "ProcessLens API",
        "version": "2.0.0",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }