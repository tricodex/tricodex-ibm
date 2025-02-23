"""
ProcessLens FastAPI Application
Enhanced with proper initialization and error handling
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio
from typing import Dict, Any

# Internal imports
from db import Database
from routes import api_router, analysis, health, websocket
from components.agents.factory import AgentFactory
from config import Config
from utils.logging_config import setup_logging

# Initialize logging
logger = setup_logging()

startup_time: datetime = None
initialization_errors: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with enhanced error handling"""
    global startup_time, initialization_errors
    
    try:
        logger.info("Starting ProcessLens initialization...")
        start_time = datetime.now()
        
        # Validate configuration first
        config_valid, config_error = Config.validate_config()
        if not config_valid:
            raise RuntimeError(f"Configuration validation failed: {config_error}")
        
        # Connect database with retry logic
        db_connected = False
        db_error = None
        for attempt in range(3):
            try:
                await Database.connect_db()
                db_connected = True
                logger.info("Database connected successfully")
                break
            except Exception as e:
                db_error = str(e)
                if attempt < 2:
                    logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Database connection failed after {attempt + 1} attempts")
        
        if not db_connected:
            raise RuntimeError(f"Database initialization failed: {db_error}")

        # Initialize agents with proper error handling
        agents_success, agents_error = await AgentFactory.initialize_agents()
        if not agents_success:
            raise RuntimeError(f"Agent initialization failed: {agents_error}")

        # Record successful startup
        startup_time = datetime.now()
        initialization_duration = (startup_time - start_time).total_seconds()
        logger.info(f"ProcessLens initialized successfully in {initialization_duration:.2f} seconds")
        
        yield
        
    except Exception as e:
        initialization_errors = {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "details": {
                "database_status": "connected" if db_connected else "failed",
                "agents_status": AgentFactory.get_agent_status()
            }
        }
        logger.error("ProcessLens initialization failed", exc_info=True)
        raise
        
    finally:
        logger.info("Starting ProcessLens shutdown...")
        try:
            await Database.close_db()
            AgentFactory.reset_agents()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Initialize FastAPI application
app = FastAPI(
    title="ProcessLens API",
    description="Process Mining and Analysis with IBM Granite",
    version=Config.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
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
async def security_headers_middleware(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers.update({
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'"
    })
    return response

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    """Global error handling middleware"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(e) if app.debug else "An unexpected error occurred"
            }
        )

# Include API routers
app.include_router(api_router)
app.include_router(analysis.router, prefix="/analyze", tags=["analysis"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Root endpoint
@app.get("/")
async def root():
    """API root information with enhanced status details"""
    if initialization_errors:
        return {
            "name": "ProcessLens API",
            "version": Config.API_VERSION,
            "status": "error",
            "error": initialization_errors,
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    
    return {
        "name": "ProcessLens API",
        "version": Config.API_VERSION,
        "status": "running",
        "uptime": (datetime.now() - startup_time).total_seconds() if startup_time else None,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "agents": AgentFactory.get_agent_status()
    }

# Startup status endpoint
@app.get("/status")
async def startup_status():
    """Get detailed API startup status"""
    return {
        "status": "error" if initialization_errors else "running",
        "startup_time": startup_time.isoformat() if startup_time else None,
        "initialization_errors": initialization_errors,
        "agents": AgentFactory.get_agent_status(),
        "database": {"connected": Database.db is not None},
        "config": Config.get_api_config()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )