"""
Health check routes for system monitoring
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime
import logging
from db import Database
from components.agents.factory import AgentFactory
from dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def health_check(db = Depends(get_db)) -> Dict[str, Any]:
    """Check overall system health"""
    try:
        # Check database connection
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check LLM agents
    agent_status = {}
    for agent_type in ["watson", "gemini"]:
        try:
            agent = AgentFactory.get_agent(agent_type)
            agent_status[agent_type] = "healthy" if agent else "not_initialized"
        except Exception as e:
            logger.error(f"{agent_type} agent health check failed: {e}")
            agent_status[agent_type] = "unhealthy"

    status = "healthy" if db_status == "healthy" and all(
        status == "healthy" for status in agent_status.values()
    ) else "degraded"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "agents": agent_status
        }
    }

@router.get("/database")
async def database_health(db = Depends(get_db)) -> Dict[str, Any]:
    """Check database health and performance"""
    try:
        start_time = datetime.utcnow()
        await db.command("ping")
        latency = (datetime.utcnow() - start_time).total_seconds()

        # Get database stats
        stats = await db.command("dbStats")
        
        return {
            "status": "healthy",
            "latency": latency,
            "collections": stats.get("collections", 0),
            "data_size": stats.get("dataSize", 0),
            "storage_size": stats.get("storageSize", 0)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.get("/models")
async def model_health() -> Dict[str, Any]:
    """Check LLM models health"""
    model_status = {}
    
    for agent_type in ["watson", "gemini"]:
        try:
            agent = AgentFactory.get_agent(agent_type)
            if not agent:
                model_status[agent_type] = {
                    "status": "not_initialized",
                    "error": None
                }
                continue

            # Simple health check with timeout
            result = await asyncio.wait_for(
                agent.analyze({"type": "health_check"}),
                timeout=5.0
            )
            
            model_status[agent_type] = {
                "status": "healthy",
                "latency": result.get("latency", 0),
                "error": None
            }
            
        except asyncio.TimeoutError:
            model_status[agent_type] = {
                "status": "timeout",
                "error": "Request timed out"
            }
        except Exception as e:
            model_status[agent_type] = {
                "status": "unhealthy",
                "error": str(e)
            }

    overall_status = "healthy" if all(
        info["status"] == "healthy" 
        for info in model_status.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "models": model_status
    }