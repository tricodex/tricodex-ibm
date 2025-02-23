"""
ProcessLens service layer for business logic
"""
from typing import Dict, Any, Optional
import pandas as pd
from bson import ObjectId
from datetime import datetime
import logging
from db import Database
from storage import GridFSStorage
from components.pipeline.analysis_pipeline import EnhancedAnalysisPipeline
from utils.helpers import ProcessLensError
from utils.serializer import serialize_analysis_results, deserialize_analysis_results
logger = logging.getLogger(__name__)

class AnalysisService:
    """Service layer for handling analysis operations"""
    
    def __init__(self, db: Database, storage: GridFSStorage, pipeline: EnhancedAnalysisPipeline):
        self.db = db
        self.storage = storage
        self.pipeline = pipeline
    
    async def start_analysis(self, file_content: bytes, filename: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new analysis task"""
        try:
            logger.info(f"Starting analysis service for file: {filename}")
            # Save file
            metadata['upload_date'] = datetime.utcnow().isoformat()
            file_id = await self.storage.save_file(file_content, filename, metadata)
            logger.info(f"File saved with ID: {file_id}")
            
            # Create task record
            task_id = ObjectId()
            await self.db.analyses.insert_one({
                "_id": task_id,
                "file_id": file_id,
                "status": "processing",
                "progress": 0,
                "created_at": datetime.utcnow(),
                "metadata": metadata,
                "thoughts": []
            })
            logger.info(f"Analysis task created with ID: {task_id}")
            
            return {
                "task_id": str(task_id),
                "file_id": file_id,
                "status": "processing",
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to start analysis: {str(e)}", exc_info=True)
            raise ProcessLensError("Failed to start analysis", {"error": str(e)})
    
    async def process_analysis(self, task_id: str, file_id: ObjectId) -> Dict[str, Any]:
        """Process analysis task with proper serialization"""
        try:
            logger.info(f"Processing analysis task: {task_id}, file: {file_id}")
            
            # Get file content as DataFrame
            df = await self.storage.get_dataframe(file_id)
            logger.info(f"Loaded DataFrame with shape: {df.shape}")
            
            # Run analysis with caching
            cache_key = f"analysis_{task_id}"
            results = await self.pipeline.analyze_dataset(df, cache_key)
            logger.info(f"Analysis completed for task: {task_id}")
            
            # Serialize results for MongoDB
            serialized_results = serialize_analysis_results(results)
            
            # Update analysis record
            await self.db.analyses.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "status": "completed",
                        "results": serialized_results,
                        "completed_at": datetime.utcnow().isoformat(),
                        "progress": 100
                    }
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis processing failed for task {task_id}: {str(e)}", exc_info=True)
            await self.db.analyses.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "completed_at": datetime.utcnow().isoformat()
                    }
                }
            )
            raise ProcessLensError(f"Analysis processing failed: {str(e)}")
    
    async def get_analysis_status(self, task_id: str) -> Dict[str, Any]:
        """Get analysis task status with deserialization"""
        try:
            analysis = await self.db.analyses.find_one({"_id": ObjectId(task_id)})
            if not analysis:
                raise ProcessLensError("Analysis task not found", {"task_id": task_id})
            
            # Deserialize results if present
            if "results" in analysis:
                analysis["results"] = deserialize_analysis_results(analysis["results"])
                
            return {
                "task_id": str(analysis["_id"]),
                "status": analysis["status"],
                "progress": analysis.get("progress", 0),
                "results": analysis.get("results"),
                "error": analysis.get("error"),
                "metadata": analysis.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get analysis status: {e}")
            raise ProcessLensError("Failed to get analysis status", {"error": str(e)})