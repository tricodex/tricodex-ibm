"""
Analysis routes with dependency injection
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, status, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from services.analysis_service import AnalysisService
from utils.helpers import ProcessLensError, format_error_response
from dependencies import get_analysis_service
from bson import ObjectId
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)
router = APIRouter()

def serialize_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize response data to ensure JSON compatibility"""
    return json.loads(json.dumps(data, default=str))

@router.post("/analyze")
async def start_analysis(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    project_name: str = Form(None)
) -> JSONResponse:
    try:
        logger.info(f"Starting analysis for file: {file.filename}")
        service = AnalysisService()
        task_id = await service.start_analysis(file, project_name)
        
        # Start background analysis task
        background_tasks.add_task(service.process_analysis, task_id)
        
        return JSONResponse(
            status_code=202,
            content=serialize_response({
                "status": "accepted",
                "task_id": task_id,
                "message": "Analysis started successfully"
            })
        )
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{task_id}")
async def get_analysis_status(task_id: str) -> JSONResponse:
    try:
        service = AnalysisService()
        status = await service.get_analysis_status(task_id)
        return JSONResponse(content=serialize_response(status))
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))