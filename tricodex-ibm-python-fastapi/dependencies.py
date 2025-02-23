"""
FastAPI dependency injection configuration
"""
import asyncio
from typing import Any, AsyncGenerator, Dict, List
from fastapi import Depends, WebSocket, HTTPException, status
import logging
from db import Database
from storage import GridFSStorage
from services.analysis_service import AnalysisService
from components.agents.factory import AgentFactory
from components.pipeline.analysis_pipeline import EnhancedAnalysisPipeline
from config import Config

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket connection manager"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str):
        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = []
            self.active_connections[task_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, task_id: str):
        async with self._lock:
            if task_id in self.active_connections:
                self.active_connections[task_id].remove(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]

    async def broadcast_update(self, task_id: str, data: Dict[str, Any]):
        if task_id in self.active_connections:
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_json(data)
                except:
                    await self.disconnect(websocket, task_id)

# Global instances
_connection_manager = ConnectionManager()

async def get_db() -> AsyncGenerator:
    """Get database connection"""
    if Database.db is None:  # Changed from 'if not Database.db' to proper None check
        await Database.connect_db()
    try:
        yield Database.db
    finally:
        # Connection will be handled by Database class
        pass

async def get_storage(db = Depends(get_db)) -> GridFSStorage:
    """Get GridFS storage instance"""
    return GridFSStorage(db)

async def get_analysis_pipeline() -> EnhancedAnalysisPipeline:
    """Get analysis pipeline instance"""
    try:
        # Get pre-initialized agents
        watson_agent = AgentFactory.get_agent("watson")
        gemini_agent = AgentFactory.get_agent("gemini")
        
        if not watson_agent or not gemini_agent:
            logger.error("Required agents not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Analysis service not ready - agents not initialized"
            )
            
        pipeline = EnhancedAnalysisPipeline(
            watson_agent=watson_agent,
            gemini_agent=gemini_agent
        )
        return pipeline
        
    except Exception as e:
        logger.error(f"Failed to initialize analysis pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def get_analysis_service(
    db = Depends(get_db),
    storage = Depends(get_storage),
    pipeline = Depends(get_analysis_pipeline)
) -> AnalysisService:
    """Get analysis service instance"""
    try:
        return AnalysisService(db, storage, pipeline)
    except Exception as e:
        logger.error(f"Failed to initialize analysis service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def get_connection_manager() -> ConnectionManager:
    """Get WebSocket connection manager instance"""
    return _connection_manager