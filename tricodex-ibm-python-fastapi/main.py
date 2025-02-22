"""
ProcessLens FastAPI Server with GridFS integration and WebSocket support
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
import os
import io
import json
from json import JSONEncoder
import logging
import pandas as pd
import asyncio
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_ibm import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from storage import GridFSStorage
from processlens import ProcessLens
from db import Database
import threading
from contextlib import asynccontextmanager

# Custom JSON encoder for ObjectId
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define lifespan before app initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    GlobalState._db = await Database.connect_db()
    GlobalState._storage = GridFSStorage(GlobalState._db)
    try:
        yield
    finally:
        # Shutdown
        await Database.close_db()
        GlobalState._process_lens = None
        GlobalState._storage = None

# Global instances
class GlobalState:
    _process_lens: Optional[ProcessLens] = None
    _db = None
    _storage = None
    _lock = threading.Lock()

    @classmethod
    def get_process_lens(cls):
        if cls._process_lens is None:
            with cls._lock:
                if cls._process_lens is None:  # Double-check pattern
                    try:
                        model = WatsonxLLM(
                            model_id="ibm/granite-3-8b-instruct",
                            apikey=os.getenv("IBM_API_KEY"),
                            project_id=os.getenv("PROJECT_ID"),
                            url=os.getenv("WATSONX_URL")
                        )
                        cls._process_lens = ProcessLens(model)
                    except Exception as e:
                        logger.error(f"Failed to initialize ProcessLens: {e}")
                        raise
        return cls._process_lens

    @classmethod
    async def get_storage(cls):
        """Get or initialize GridFS storage"""
        if cls._storage is None:
            cls._storage = GridFSStorage(cls._db)
        return cls._storage

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = []
            self.active_connections[task_id].append(websocket)
            logger.info(f"New WebSocket connection for task {task_id}")
        
    async def disconnect(self, websocket: WebSocket, task_id: str):
        async with self._lock:
            if task_id in self.active_connections:
                try:
                    self.active_connections[task_id].remove(websocket)
                    if not self.active_connections[task_id]:
                        del self.active_connections[task_id]
                    logger.info(f"WebSocket disconnected for task {task_id}")
                except ValueError:
                    pass
                
    async def broadcast_update(self, task_id: str, data: Dict[str, Any]):
        async with self._lock:
            if task_id in self.active_connections:
                dead_ws = []
                for websocket in self.active_connections[task_id]:
                    try:
                        await websocket.send_json(data)
                    except Exception as e:
                        logger.error(f"Error sending WebSocket message: {e}")
                        dead_ws.append(websocket)
                
                # Cleanup dead connections
                for ws in dead_ws:
                    await self.disconnect(ws, task_id)

# Initialize FastAPI with lifespan
app = FastAPI(
    title="ProcessLens API",
    description="API for process mining and optimization using IBM Granite",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize connection manager
manager = ConnectionManager()

# Add CORS middleware after app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "X-Content-Range"]
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ProcessLens FastAPI is running.",
        "status": "healthy"
    }

@app.post("/analyze")
async def analyze_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_name: str = None
):
    """
    Upload and analyze a process dataset
    Returns a task ID for status tracking
    """
    try:
        # Get file content
        contents = await file.read()
        
        # Prepare metadata
        metadata = {
            "content_type": file.content_type,
            "project_name": project_name,
            "original_filename": file.filename,
            "upload_date": datetime.utcnow().isoformat()
        }
        
        # Save to GridFS
        storage = await GlobalState.get_storage()
        file_id = await storage.save_file(contents, file.filename, metadata)
        
        # Create task ID and project info
        task_id = str(ObjectId())
        project_info = {
            "name": project_name or file.filename,
            "created_at": datetime.utcnow().isoformat(),
            "file_type": file.content_type,
            "file_id": str(file_id)
        }
        
        # Store initial analysis info
        await GlobalState._db.analyses.insert_one({
            "_id": ObjectId(task_id),
            "status": "processing",
            "progress": 0,
            "thoughts": [],
            "project": project_info,
            "file_id": file_id
        })
        
        # Start background analysis
        background_tasks.add_task(
            analyze_in_background,
            task_id=task_id,
            file_id=file_id
        )
        
        return JSONResponse(
            content={
                "message": "Analysis started",
                "task_id": task_id,
                "project": project_info
            },
            status_code=202
        )
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time analysis updates"""
    try:
        # Accept connection first
        await websocket.accept()
        logger.info(f"WebSocket connection established for task {task_id}")
        
        # Then add to manager
        await manager.connect(websocket, task_id)
        
        # Send initial state
        analysis = await GlobalState._db.analyses.find_one({"_id": ObjectId(task_id)})
        if analysis:
            if analysis.get('thoughts'):
                for thought in analysis.get('thoughts', []):
                    await websocket.send_json({
                        'type': 'thought_update',
                        'data': thought
                    })
            
            if analysis.get('status') == 'completed':
                await websocket.send_json({
                    'type': 'analysis_complete',
                    'data': {
                        'results': analysis.get('results'),
                        'completed_at': analysis.get('completed_at')
                    }
                })
            elif analysis.get('status') == 'failed':
                await websocket.send_json({
                    'type': 'analysis_error',
                    'data': {'error': analysis.get('error')}
                })
        
        # Keep connection alive until client disconnects
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {task_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected during handshake: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        await manager.disconnect(websocket, task_id)

async def analyze_in_background(task_id: str, file_id: ObjectId):
    try:
        # Get file from GridFS and convert to DataFrame 
        storage = await GlobalState.get_storage()
        df = await storage.get_dataframe(file_id)
        
        # Initialize WatsonX LLM with correct credential format
        model_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 1024,
            "min_new_tokens": 1,
            "repetition_penalty": 1.2,
            "temperature": 0.7
        }
        
        # Changed: Pass credentials directly instead of nested dict
        granite_model = WatsonxLLM(
            model_id="ibm/granite-3-8b-instruct",
            apikey=os.getenv("IBM_API_KEY"),  # Direct parameter
            url=os.getenv("WATSONX_URL"),     # Direct parameter
            project_id=os.getenv("PROJECT_ID"),
            params=model_params
        )
        
        process_lens = ProcessLens(granite_model)
        
        async def thought_callback(stage: str, thought: str):
            stages_info = {
                "structure_analysis": {"progress": 20, "prefix": "📊"},
                "pattern_mining": {"progress": 40, "prefix": "🔄"},
                "performance_analysis": {"progress": 60, "prefix": "⚡"},
                "improvement_generation": {"progress": 80, "prefix": "📈"},
                "final_synthesis": {"progress": 100, "prefix": "💡"}
            }
            
            stage_info = stages_info.get(stage, {"progress": 0, "prefix": ""})
            
            # Create thought data
            thought_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "stage": stage,
                "thought": f"{stage_info['prefix']} {thought}",
                "progress": stage_info['progress']
            }
            
            # Update MongoDB
            await GlobalState._db.analyses.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$push": {"thoughts": thought_data},
                    "$set": {"progress": stage_info['progress']}
                }
            )
            
            # Send WebSocket update
            await manager.broadcast_update(task_id, {
                "type": "thought_update",
                "data": thought_data
            })
        
        # Run analysis with thought tracking
        results = await process_lens.analyze_dataset(df, thought_callback=thought_callback)
        
        # Update MongoDB with final results
        update_data = {
            "status": "completed",
            "results": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await GlobalState._db.analyses.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
        
        # Send completion WebSocket update
        await manager.broadcast_update(task_id, {
            "type": "analysis_complete",
            "data": update_data
        })
        
        # Update file metadata
        await storage.update_metadata(file_id, {
            "analysis_completed": True,
            "analysis_summary": {
                "patterns_found": len(results.get("patterns", [])),
                "metrics_analyzed": list(results.get("performance", {}).keys()),
                "completed_at": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        error_detail = str(e)
        logger.error(f"Error in background analysis: {error_detail}")
        
        # Update MongoDB with error status
        error_update = {
            "status": "failed",
            "error": error_detail,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await GlobalState._db.analyses.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": error_update}
        )
        
        # Send error WebSocket update
        await manager.broadcast_update(task_id, {
            "type": "analysis_error",
            "data": error_update
        })
        
        # Update file metadata
        await storage.update_metadata(file_id, {
            "analysis_completed": False,
            "analysis_error": error_detail
        })

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Get the status and results of an analysis task"""
    try:
        analysis = await GlobalState._db.analyses.find_one({"_id": ObjectId(task_id)})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return JSONResponse(
            content=json.loads(json.dumps(dict(analysis), cls=CustomJSONEncoder))
        )
    except Exception as e:
        logger.error(f"Error retrieving analysis status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analysis status: {str(e)}"
        )

@app.get("/files")
async def list_files(skip: int = 0, limit: int = 10):
    """List all uploaded files"""
    try:
        storage = await GlobalState.get_storage()
        files = await storage.list_files(skip=skip, limit=limit)
        return JSONResponse(content=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get file metadata"""
    try:
        storage = await GlobalState.get_storage()
        metadata = await storage.get_metadata(ObjectId(file_id))
        return JSONResponse(content=metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    try:
        storage = await GlobalState.get_storage()
        success = await storage.delete_file(ObjectId(file_id))
        if success:
            return JSONResponse(content={"message": "File deleted successfully"})
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/cleanup")
async def cleanup_old_data(days: int = 30):
    """Clean up old analyses and files"""
    try:
        storage = await GlobalState.get_storage()
        deleted_files = await storage.cleanup_old_files(days)
        deleted_analyses = await Database.cleanup_old_analyses(days)
        
        return {
            "message": "Cleanup completed",
            "deleted_files": deleted_files,
            "deleted_analyses": deleted_analyses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)