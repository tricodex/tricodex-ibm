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
from utils.helpers import format_error_response, ProcessLensError
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super().default(obj)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections[task_id] = websocket
            logger.info(f"WebSocket connection established for task: {task_id}")
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            raise
    
    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]
            logger.info(f"WebSocket disconnected: {task_id}")

    async def send_message(self, task_id: str, message: Dict[str, Any]):
        """Send formatted message to client"""
        if task_id in self.active_connections:
            try:
                # Ensure message has required structure
                formatted_message = {
                    "type": message.get("type", "status_update"),
                    "data": {
                        "taskId": task_id,
                        "status": message.get("status", "processing"),
                        "progress": message.get("progress", 0),
                        "thoughts": message.get("thoughts", []),
                        "results": message.get("results"),
                        "error": message.get("error")
                    }
                }
                
                # Convert all timestamps to ISO format
                if "thoughts" in formatted_message["data"]:
                    for thought in formatted_message["data"]["thoughts"]:
                        if "timestamp" in thought:
                            thought["timestamp"] = thought["timestamp"].isoformat()

                await self.active_connections[task_id].send_text(
                    json.dumps(formatted_message)
                )
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

manager = ConnectionManager()

@router.websocket("/{task_id}")
async def analysis_updates(
    websocket: WebSocket,
    task_id: str,
    connection_manager = Depends(get_connection_manager),
    service: Optional[AnalysisService] = Depends(get_analysis_service)
):
    """WebSocket endpoint with enhanced error handling"""
    try:
        await manager.connect(task_id, websocket)
        
        # Send initial state with error handling
        if service:
            try:
                status = await service.get_analysis_status(task_id)
                if status:
                    await manager.send_message(task_id, {
                        "type": "initial_state",
                        **status
                    })
            except Exception as e:
                logger.error(f"Failed to get initial status: {e}")
                await manager.send_message(task_id, {
                    "type": "error",
                    "error": format_error_response(e)
                })
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "status_request" and service:
                    try:
                        status = await service.get_analysis_status(task_id)
                        if status:
                            await manager.send_message(task_id, {
                                "type": "status_update",
                                **status
                            })
                    except Exception as e:
                        logger.error(f"Status request failed: {e}")
                        await manager.send_message(task_id, {
                            "type": "error",
                            "error": format_error_response(e)
                        })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {task_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                try:
                    await manager.send_message(task_id, {
                        "type": "error",
                        "error": format_error_response(e)
                    })
                except:
                    pass  # If sending error fails, just break the connection
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(task_id)