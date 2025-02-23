"""
WebSocket routes and connection management
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
from datetime import datetime
from services.analysis_service import AnalysisService
from dependencies import get_analysis_service, get_connection_manager
from utils.helpers import format_error_response
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter()

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
        logger.info(f"WebSocket connection established for task: {task_id}")

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]
            logger.info(f"WebSocket disconnected: {task_id}")

    async def send_update(self, task_id: str, data: Dict[str, Any]):
        if task_id in self.active_connections:
            try:
                sanitized_data = self._sanitize_data(data)
                await self.active_connections[task_id].send_json(sanitized_data)
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
                # Don't re-raise, just log the error
                
    def _sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data for JSON serialization"""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, (pd.Timestamp, datetime)):
            return data.isoformat()
        elif pd.isna(data):
            return None
        return data

manager = ConnectionManager()

@router.websocket("/{task_id}")
async def analysis_updates(
    websocket: WebSocket,
    task_id: str,
    connection_manager = Depends(get_connection_manager),
    service: Optional[AnalysisService] = Depends(get_analysis_service)
):
    """WebSocket endpoint for real-time analysis updates"""
    try:
        await manager.connect(task_id, websocket)
        
        # Send initial state
        if service:
            status = await service.get_analysis_status(task_id)
            await manager.send_update(task_id, {
                "type": "initial_state",
                "data": status
            })
        
        # Handle client messages
        try:
            while True:
                data = await websocket.receive_json()
                
                # Handle different message types
                if data.get("type") == "ping":
                    await manager.send_update(task_id, {"type": "pong"})
                elif data.get("type") == "status_request" and service:
                    status = await service.get_analysis_status(task_id)
                    await manager.send_update(task_id, {
                        "type": "status_update",
                        "data": status
                    })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {task_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await manager.send_update(task_id, {
                "type": "error",
                "data": format_error_response(e)
            })
            
    finally:
        manager.disconnect(task_id)