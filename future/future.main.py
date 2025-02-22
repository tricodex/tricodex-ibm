
# import os
# import pandas as pd
# from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse, StreamingResponse
# from dotenv import load_dotenv
# from langchain_ibm import WatsonxLLM
# from processlens import ProcessLens
# import logging
# from typing import Optional, Dict, Any, List
# import json
# from datetime import datetime
# from bson import ObjectId
# import io
# import openpyxl
# import chardet
# import motor.motor_asyncio
# from db import Database
# from storage import IBMCloudStorage

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Global ProcessLens instance
# _process_lens: Optional[ProcessLens] = None

# # Initialize FastAPI app
# app = FastAPI(
#     title="ProcessLens API",
#     description="API for process mining and optimization using IBM Granite",
#     version="1.0.0"
# )

# # Add CORS middleware for Nextjs frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # Add your Next.js frontend URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["Content-Range", "X-Content-Range"]
# )

# # Add security headers middleware
# @app.middleware("http")
# async def add_security_headers(request, call_next):
#     response = await call_next(request)
#     response.headers["X-Frame-Options"] = "DENY"
#     response.headers["X-Content-Type-Options"] = "nosniff"
#     response.headers["X-XSS-Protection"] = "1; mode=block"
#     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
#     return response

# # MongoDB configuration
# MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://your-cluster.mongodb.net")
# client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
# db = client.processlens_db

# # Store background tasks results
# analysis_results = {}

# # Helper function to initialize WatsonxLLM and ProcessLens
# def get_process_lens():
#     """Get or initialize ProcessLens instance with proper error handling"""
#     global _process_lens
    
#     try:
#         if (_process_lens is None):
#             logger.info("Initializing ProcessLens...")
#             model_parameters = {
#                 "decoding_method": "greedy",
#                 "max_new_tokens": 1000,
#                 "min_new_tokens": 1,
#                 "temperature": 0.7,
#                 "repetition_penalty": 1.1
#             }
            
#             model = WatsonxLLM(
#                 model_id="ibm/granite-3-8b-instruct",
#                 credentials={
#                     "url": os.getenv("WATSONX_URL"),
#                     "apikey": os.getenv("IBM_API_KEY")
#                 },
#                 project_id=os.getenv("PROJECT_ID"),
#                 params=model_parameters
#             )
            
#             _process_lens = ProcessLens(model)
#             logger.info("ProcessLens initialized successfully")
            
#         return _process_lens
#     except Exception as e:
#         logger.error(f"Error initializing ProcessLens: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail={"error": "Error initializing ProcessLens", "details": str(e)}
#         )

# async def parse_document(file: UploadFile) -> pd.DataFrame:
#     """Parse different document formats into a pandas DataFrame"""
#     contents = await file.read()
    
#     if file.content_type == "text/csv":
#         # Detect encoding
#         encoding = chardet.detect(contents)['encoding']
#         return pd.read_csv(io.StringIO(contents.decode(encoding)))
    
#     elif file.content_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
#         return pd.read_excel(io.BytesIO(contents))
    
#     elif file.content_type == "application/json":
#         return pd.DataFrame(json.loads(contents.decode('utf-8')))
    
#     elif file.content_type == "text/xml":
#         return pd.read_xml(io.StringIO(contents.decode('utf-8')))
    
#     else:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Unsupported file type: {file.content_type}. Supported types: CSV, Excel, JSON, XML"
#         )

# class JSONEncoder(json.JSONEncoder):
#     """Custom JSON encoder for MongoDB ObjectId and datetime objects"""
#     def default(self, obj):
#         if isinstance(obj, ObjectId):
#             return str(obj)
#         if isinstance(obj, datetime):
#             return obj.isoformat()
#         return super().default(obj)

# # Background task for analysis
# async def analyze_in_background(task_id: str, df: pd.DataFrame):
#     """Background task that handles process analysis and captures model thoughts"""
#     try:
#         process_lens = get_process_lens()
        
#         async def thought_callback(stage: str, thought: str):
#             stages_info = {
#                 "structure_analysis": {"progress": 20, "prompt_prefix": "Dataset Structure 📊: "},
#                 "pattern_mining": {"progress": 40, "prompt_prefix": "Process Pattern 🔄: "},
#                 "performance_analysis": {"progress": 60, "prompt_prefix": "Performance Metric ⚡: "},
#                 "improvement_generation": {"progress": 80, "prompt_prefix": "Improvement 📈: "},
#                 "final_synthesis": {"progress": 100, "prompt_prefix": "Key Insights 💡: "}
#             }
            
#             stage_info = stages_info.get(stage, {"progress": 0, "prompt_prefix": ""})
            
#             # Update MongoDB with new thought
#             await db.analyses.update_one(
#                 {"_id": ObjectId(task_id)},
#                 {
#                     "$push": {
#                         "thoughts": {
#                             "timestamp": datetime.utcnow(),
#                             "stage": stage,
#                             "thought": f"{stage_info['prompt_prefix']}{thought}",
#                             "progress": stage_info['progress']
#                         }
#                     },
#                     "$set": {
#                         "progress": stage_info['progress']
#                     }
#                 }
#             )
        
#         # Run analysis with thought tracking
#         results = await process_lens.analyze_dataset(df, thought_callback=thought_callback)
        
#         # Store final results in MongoDB
#         await db.analyses.update_one(
#             {"_id": ObjectId(task_id)},
#             {
#                 "$set": {
#                     "status": "completed",
#                     "results": results,
#                     "completed_at": datetime.utcnow()
#                 }
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"Error in background analysis: {str(e)}")
#         await db.analyses.update_one(
#             {"_id": ObjectId(task_id)},
#             {
#                 "$set": {
#                     "status": "failed",
#                     "error": str(e)
#                 }
#             }
#         )

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "message": "ProcessLens FastAPI is running.",
#         "status": "healthy"
#     }

# # Initialize storage service
# storage_service = IBMCloudStorage()

# @app.post("/analyze")
# async def analyze_dataset(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...),
#     project_name: str = None
# ):
#     """
#     Analyze a process dataset from various document formats
#     Returns a task ID that can be used to check the analysis status
#     """
#     try:
#         # Read file content
#         contents = await file.read()
#         file_size = len(contents)
        
#         # Check file size
#         max_size = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB default
#         if file_size > max_size:
#             raise HTTPException(
#                 status_code=413,
#                 detail=f"File too large. Maximum size is {max_size/1048576:.1f}MB"
#             )
        
#         # Generate task ID
#         task_id = str(ObjectId())
        
#         # Prepare metadata for IBM COS
#         metadata = {
#             'task_id': task_id,
#             'project_name': project_name or file.filename,
#             'content_type': file.content_type,
#             'upload_time': datetime.utcnow().isoformat()
#         }
        
#         # Upload to IBM COS
#         cos_key = await storage_service.upload_file(
#             file_content=contents,
#             file_name=file.filename,
#             metadata=metadata
#         )
        
#         # Create document record in MongoDB
#         document_info = {
#             "_id": ObjectId(task_id),
#             "fileName": file.filename,
#             "fileType": file.content_type,
#             "uploadedAt": datetime.utcnow(),
#             "size": file_size,
#             "cosKey": cos_key,
#             "status": "pending",
#             "project": {
#                 "name": project_name or file.filename,
#                 "created_at": datetime.utcnow()
#             }
#         }
        
#         await db.documents.insert_one(document_info)
        
#         # Start background processing
#         background_tasks.add_task(process_document, task_id, cos_key)
        
#         return JSONResponse(
#             content={
#                 "message": "Document uploaded and queued for processing",
#                 "task_id": task_id,
#                 "document": {
#                     "name": file.filename,
#                     "type": file.content_type,
#                     "size": file_size
#                 }
#             },
#             status_code=202
#         )
        
#     except Exception as e:
#         logger.error(f"Error handling file upload: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing upload: {str(e)}"
#         )

# async def process_document(task_id: str, cos_key: str):
#     """Background task to process uploaded document"""
#     try:
#         # Update status to processing
#         await db.documents.update_one(
#             {"_id": ObjectId(task_id)},
#             {"$set": {"status": "processing"}}
#         )
        
#         # Get file from IBM COS
#         file_content = await storage_service.get_file(cos_key)
        
#         # Get metadata to determine file type
#         metadata = await storage_service.get_file_metadata(cos_key)
#         content_type = metadata['content_type']
        
#         # Create DataFrame based on file type
#         if content_type == 'text/csv':
#             df = pd.read_csv(io.BytesIO(file_content))
#         elif content_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
#             df = pd.read_excel(io.BytesIO(file_content))
#         elif content_type == 'application/json':
#             df = pd.DataFrame(json.loads(file_content.decode('utf-8')))
#         else:
#             raise ValueError(f"Unsupported file type: {content_type}")
        
#         # Process with ProcessLens
#         process_lens = get_process_lens()
        
#         async def thought_callback(stage: str, thought: str):
#             await db.documents.update_one(
#                 {"_id": ObjectId(task_id)},
#                 {
#                     "$push": {
#                         "thoughts": {
#                             "timestamp": datetime.utcnow(),
#                             "stage": stage,
#                             "thought": thought
#                         }
#                     }
#                 }
#             )
        
#         results = await process_lens.analyze_dataset(
#             df,
#             thought_callback=thought_callback
#         )
        
#         # Store results and update status
#         await db.documents.update_one(
#             {"_id": ObjectId(task_id)},
#             {
#                 "$set": {
#                     "status": "processed",
#                     "processedData": results,
#                     "processedAt": datetime.utcnow()
#                 }
#             }
#         )
        
#         # Optionally cleanup the original file if not needed
#         # await storage_service.delete_file(cos_key)
        
#     except Exception as e:
#         logger.error(f"Error processing document: {str(e)}")
#         await db.documents.update_one(
#             {"_id": ObjectId(task_id)},
#             {
#                 "$set": {
#                     "status": "failed",
#                     "error": str(e)
#                 }
#             }
#         )

# @app.get("/download/{task_id}")
# async def download_processed_file(task_id: str):
#     """Download processed file results"""
#     try:
#         document = await db.documents.find_one({"_id": ObjectId(task_id)})
#         if not document:
#             raise HTTPException(status_code=404, detail="Document not found")
            
#         if document['status'] != 'processed':
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Document is not ready. Current status: {document['status']}"
#             )
            
#         # Get the original file from IBM COS
#         cos_key = document['cosKey']
#         file_content = await storage_service.get_file(cos_key)
        
#         return StreamingResponse(
#             io.BytesIO(file_content),
#             media_type=document['fileType'],
#             headers={
#                 'Content-Disposition': f'attachment; filename="{document["fileName"]}"'
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"Error downloading file: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error downloading file: {str(e)}"
#         )

# @app.get("/status/{task_id}")
# async def get_analysis_status(task_id: str):
#     """Get the status and results of an analysis task"""
#     analysis = await db.analyses.find_one({"_id": ObjectId(task_id)})
#     if not analysis:
#         raise HTTPException(
#             status_code=404,
#             detail="Analysis task not found"
#         )
    
#     return JSONResponse(content=json.loads(json.dumps(analysis, cls=JSONEncoder)))

# @app.get("/projects")
# async def list_projects(skip: int = 0, limit: int = 10):
#     """List all analysis projects"""
#     cursor = db.analyses.find({}).sort("created_at", -1).skip(skip).limit(limit)
#     projects = await cursor.to_list(length=limit)
#     return JSONResponse(content=json.loads(json.dumps(projects, cls=JSONEncoder)))

# @app.get("/health")
# async def health_check():
#     """Detailed health check endpoint"""
#     try:
#         # Test ProcessLens initialization
#         process_lens = get_process_lens()
#         return {
#             "status": "healthy",
#             "components": {
#                 "ProcessLens": "operational",
#                 "IBM_Granite": "connected"
#             }
#         }
#     except Exception as e:
#         return JSONResponse(
#             content={
#                 "status": "unhealthy",
#                 "error": str(e)
#             },
#             status_code=503
#         )

# # Error handlers
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "error": exc.detail,
#             "status_code": exc.status_code
#         }
#     )

# @app.exception_handler(Exception)
# async def general_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": str(exc),
#             "status_code": 500
#         }
#     )

# # Agent-specific endpoints
# @app.post("/analyze/timing")
# async def analyze_timing(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):
#     """Analyze timing metrics for a process dataset"""
#     try:
#         contents = await file.read()
#         df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
#         process_lens = get_process_lens()
#         timing_agent = process_lens.optimizer.metrics_agents["timing"]
#         results = await timing_agent.analyze(df)
        
#         return JSONResponse(content=results)
#     except Exception as e:
#         logger.error(f"Error in timing analysis: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/analyze/quality")
# async def analyze_quality(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):
#     """Analyze quality metrics for a process dataset"""
#     try:
#         contents = await file.read()
#         df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
#         process_lens = get_process_lens()
#         quality_agent = process_lens.optimizer.metrics_agents["quality"]
#         results = await quality_agent.analyze(df)
        
#         return JSONResponse(content=results)
#     except Exception as e:
#         logger.error(f"Error in quality analysis: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/analyze/resources")
# async def analyze_resources(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):
#     """Analyze resource utilization metrics for a process dataset"""
#     try:
#         contents = await file.read()
#         df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
#         process_lens = get_process_lens()
#         resource_agent = process_lens.optimizer.metrics_agents["resource"]
#         results = await resource_agent.analyze(df)
        
#         return JSONResponse(content=results)
#     except Exception as e:
#         logger.error(f"Error in resource analysis: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# # Startup and shutdown events
# @app.on_event("startup")
# async def startup_db_client():
#     await Database.connect_db()
#     logger.info("ProcessLens API started, database connected")

# @app.on_event("shutdown")
# async def shutdown_db_client():
#     await Database.close_db()
#     logger.info("ProcessLens API shutdown, database disconnected")

# # Add storage cleanup task
# @app.post("/admin/cleanup")
# async def cleanup_old_data(days: int = 30):
#     """Clean up old analyses data"""
#     try:
#         await Database.cleanup_old_analyses(days)
#         return {"message": f"Successfully cleaned up analyses older than {days} days"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)