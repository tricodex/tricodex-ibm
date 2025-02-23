"""
Analysis routes with dependency injection
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, status, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from services.analysis_service import AnalysisService
from utils.helpers import ProcessLensError, format_error_response, validate_file_content
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

@router.post("/")  # Changed from /analyze to / since the prefix will be /analyze
async def start_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(None),
    service: AnalysisService = Depends(get_analysis_service)
) -> JSONResponse:
    try:
        logger.info(f"Starting analysis for file: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )

        # Read file content with size validation
        try:
            contents = await file.read()
            if not contents:
                raise HTTPException(
                    status_code=400,
                    detail="Empty file provided"
                )
        except Exception as e:
            logger.error(f"File read error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read file: {str(e)}"
            )

        # Validate file content
        try:
            validate_file_content(contents, file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        # Start analysis
        task_id = await service.start_analysis(
            file_content=contents,
            filename=file.filename,
            metadata={
                "project_name": project_name,
                "file_size": len(contents),
                "content_type": file.content_type
            }
        )
        
        # Start background analysis task
        background_tasks.add_task(
            service.process_analysis,
            task_id["task_id"],
            task_id["file_id"]
        )
        
        return JSONResponse(
            status_code=202,
            content=serialize_response({
                "status": "accepted",
                "task_id": task_id["task_id"],
                "message": "Analysis started successfully"
            })
        )
        
    except HTTPException as e:
        logger.error(f"Analysis request validation failed: {e.detail}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e.detail),
                "details": getattr(e, 'details', None)
            },
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Unexpected error in analysis start: {e}", exc_info=True)
        return JSONResponse(
            content={
                "status": "error",
                "error": "Internal server error",
                "details": str(e)
            },
            status_code=500
        )

@router.get("/{task_id}")  # Changed from /analyze/{task_id} to /{task_id}
async def get_analysis_status(
    task_id: str,
    service: AnalysisService = Depends(get_analysis_service)
) -> JSONResponse:
    try:
        status = await service.get_analysis_status(task_id)
        return JSONResponse(content=serialize_response(status))
    except ProcessLensError as e:
        logger.error(f"Failed to get analysis status: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "details": e.details if hasattr(e, 'details') else None
            },
            status_code=404
        )
    except Exception as e:
        logger.error(f"Unexpected error getting status: {e}", exc_info=True)
        return JSONResponse(
            content={
                "status": "error",
                "error": "Internal server error",
                "details": str(e)
            },
            status_code=500
        )