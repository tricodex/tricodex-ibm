import os
import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from langchain_ibm import WatsonxLLM
from processlens import ProcessLens
import logging
from typing import Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ProcessLens instance
_process_lens: Optional[ProcessLens] = None

# Initialize FastAPI app
app = FastAPI(
    title="ProcessLens API",
    description="API for process mining and optimization using IBM Granite",
    version="1.0.0"
)

# Add CORS middleware for Nextjs frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your Next.js frontend URL
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

# Store background tasks results
analysis_results = {}

# Helper function to initialize WatsonxLLM and ProcessLens
def get_process_lens():
    """Get or initialize ProcessLens instance with proper error handling"""
    global _process_lens
    
    try:
        if (_process_lens is None):
            logger.info("Initializing ProcessLens...")
            model_parameters = {
                "decoding_method": "greedy",
                "max_new_tokens": 1000,
                "min_new_tokens": 1,
                "temperature": 0.7,
                "repetition_penalty": 1.1
            }
            
            model = WatsonxLLM(
                model_id="ibm/granite-3-8b-instruct",
                credentials={
                    "url": os.getenv("WATSONX_URL"),
                    "apikey": os.getenv("IBM_API_KEY")
                },
                project_id=os.getenv("PROJECT_ID"),
                params=model_parameters
            )
            
            _process_lens = ProcessLens(model)
            logger.info("ProcessLens initialized successfully")
            
        return _process_lens
    except Exception as e:
        logger.error(f"Error initializing ProcessLens: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error initializing ProcessLens", "details": str(e)}
        )

# Background task for analysis
async def analyze_in_background(task_id: str, df: pd.DataFrame):
    """Background task that handles process analysis and captures model thoughts"""
    try:
        process_lens = get_process_lens()
        
        # Create thought callback with structured format
        def thought_callback(stage: str, thought: str):
            stages_info = {
                "structure_analysis": {
                    "progress": 20,
                    "prompt_prefix": "Dataset Structure 📊: "
                },
                "pattern_mining": {
                    "progress": 40,
                    "prompt_prefix": "Process Pattern 🔄: "
                },
                "performance_analysis": {
                    "progress": 60,
                    "prompt_prefix": "Performance Metric ⚡: "
                },
                "improvement_generation": {
                    "progress": 80,
                    "prompt_prefix": "Improvement 📈: "
                },
                "final_synthesis": {
                    "progress": 100,
                    "prompt_prefix": "Key Insights 💡: "
                }
            }
            
            stage_info = stages_info.get(stage, {"progress": 0, "prompt_prefix": ""})
            
            analysis_results[task_id]["thoughts"].append({
                "timestamp": pd.Timestamp.now().isoformat(),
                "stage": stage,
                "thought": f"{stage_info['prompt_prefix']}{thought}",
                "progress": stage_info['progress']
            })
            analysis_results[task_id]["progress"] = stage_info['progress']
        
        # Initialize analysis with thought tracking
        analysis_results[task_id].update({
            "status": "processing",
            "progress": 0,
            "thoughts": []
        })
        
        thought_callback("initialization", "Initializing process analysis pipeline...")
        
        # Run analysis with thought tracking
        results = await process_lens.analyze_dataset(
            df,
            thought_callback=thought_callback
        )
        
        # Final success message
        thought_callback("completion", "✅ Analysis completed successfully with actionable insights ready for review.")
        
        analysis_results[task_id].update({
            "status": "completed",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in background analysis: {str(e)}")
        analysis_results[task_id].update({
            "status": "failed",
            "error": str(e),
            "thoughts": analysis_results[task_id].get("thoughts", []) + [{
                "timestamp": pd.Timestamp.now().isoformat(),
                "stage": "error",
                "thought": f"Error occurred: {str(e)}"
            }]
        })

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
    file: UploadFile = File(...)
):
    """
    Analyze a process dataset from a CSV file
    Returns a task ID that can be used to check the analysis status
    """
    if file.content_type != "text/csv":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are accepted."
        )
    
    try:
        # Read the uploaded CSV file into pandas DataFrame
        contents = await file.read()
        df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
        # Generate task ID
        task_id = f"task_{len(analysis_results)}"
        
        # Initialize task status
        analysis_results[task_id] = {
            "status": "processing",
            "progress": 0,
            "thoughts": []
        }
        
        # Start background analysis
        background_tasks.add_task(analyze_in_background, task_id, df)
        
        return JSONResponse(
            content={
                "message": "Analysis started",
                "task_id": task_id
            },
            status_code=202
        )
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Get the status and results of an analysis task"""
    if task_id not in analysis_results:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    return analysis_results[task_id]

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    try:
        # Test ProcessLens initialization
        process_lens = get_process_lens()
        return {
            "status": "healthy",
            "components": {
                "ProcessLens": "operational",
                "IBM_Granite": "connected"
            }
        }
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "status_code": 500
        }
    )

# Agent-specific endpoints
@app.post("/analyze/timing")
async def analyze_timing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Analyze timing metrics for a process dataset"""
    try:
        contents = await file.read()
        df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
        process_lens = get_process_lens()
        timing_agent = process_lens.optimizer.metrics_agents["timing"]
        results = await timing_agent.analyze(df)
        
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error in timing analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/quality")
async def analyze_quality(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Analyze quality metrics for a process dataset"""
    try:
        contents = await file.read()
        df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
        process_lens = get_process_lens()
        quality_agent = process_lens.optimizer.metrics_agents["quality"]
        results = await quality_agent.analyze(df)
        
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error in quality analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/resources")
async def analyze_resources(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Analyze resource utilization metrics for a process dataset"""
    try:
        contents = await file.read()
        df = pd.read_csv(pd.compat.StringIO(contents.decode('utf-8')))
        
        process_lens = get_process_lens()
        resource_agent = process_lens.optimizer.metrics_agents["resource"]
        results = await resource_agent.analyze(df)
        
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error in resource analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)