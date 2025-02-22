"""
Enhanced GridFS storage implementation for ProcessLens
"""
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import logging
import io
import pandas as pd
from bson import ObjectId

logger = logging.getLogger(__name__)

class GridFSStorage:
    def __init__(self, db):
        """Initialize GridFS storage with MongoDB database"""
        self.db = db
        self.fs = AsyncIOMotorGridFSBucket(db)
        self.chunk_size = 1024 * 1024  # 1MB chunks

    async def save_file(self, 
                       file_content: bytes | BinaryIO, 
                       filename: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> ObjectId:
        """
        Save file to GridFS with metadata
        Returns: ObjectId of stored file
        """
        try:
            # Prepare metadata
            file_metadata = {
                "uploaded_at": datetime.utcnow(),
                "filename": filename,
                **(metadata or {})
            }

            # Create upload stream
            grid_in = self.fs.open_upload_stream(
                filename,
                metadata=file_metadata,
                chunk_size_bytes=self.chunk_size
            )

            # Handle both bytes and file-like objects
            if isinstance(file_content, bytes):
                await grid_in.write(file_content)
            else:
                while chunk := file_content.read(self.chunk_size):
                    await grid_in.write(chunk)

            await grid_in.close()
            file_id = grid_in._id

            logger.info(f"Successfully saved file {filename} to GridFS with id {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"Error saving file to GridFS: {str(e)}")
            raise

    async def get_file(self, file_id: ObjectId) -> bytes:
        """
        Retrieve file from GridFS by ID
        Returns: File contents as bytes
        """
        try:
            grid_out = await self.fs.open_download_stream(file_id)
            contents = await grid_out.read()
            return contents
        except Exception as e:
            logger.error(f"Error retrieving file from GridFS: {str(e)}")
            raise

    async def get_dataframe(self, file_id: ObjectId) -> pd.DataFrame:
        """
        Retrieve file from GridFS and convert to pandas DataFrame
        Handles CSV, Excel, and other tabular formats
        """
        try:
            # Get file and metadata
            grid_out = await self.fs.open_download_stream(file_id)
            contents = await grid_out.read()
            metadata = grid_out.metadata
            filename = metadata.get('filename', '').lower()

            # Convert to DataFrame based on file type
            if filename.endswith('.csv'):
                return pd.read_csv(io.BytesIO(contents))
            elif filename.endswith(('.xlsx', '.xls')):
                return pd.read_excel(io.BytesIO(contents))
            elif filename.endswith('.json'):
                return pd.read_json(io.BytesIO(contents))
            else:
                raise ValueError(f"Unsupported file format: {filename}")

        except Exception as e:
            logger.error(f"Error converting file to DataFrame: {str(e)}")
            raise

    async def get_metadata(self, file_id: ObjectId) -> Dict[str, Any]:
        """Get file metadata from GridFS"""
        try:
            grid_out = await self.fs.open_download_stream(file_id)
            return {
                "filename": grid_out.filename,
                "metadata": grid_out.metadata,
                "length": grid_out.length,
                "upload_date": grid_out.upload_date,
                "content_type": grid_out.metadata.get("content_type"),
                "chunk_size": grid_out.chunk_size,
            }
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            raise

    async def delete_file(self, file_id: ObjectId) -> bool:
        """Delete file from GridFS"""
        try:
            await self.fs.delete(file_id)
            logger.info(f"Successfully deleted file {file_id} from GridFS")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

    async def list_files(self, 
                        filter_dict: Optional[Dict[str, Any]] = None, 
                        skip: int = 0, 
                        limit: int = 100) -> list:
        """List files in GridFS with optional filtering"""
        try:
            cursor = self.fs.find(
                filter=filter_dict or {},
                skip=skip,
                limit=limit,
                no_cursor_timeout=False
            )
            files = []
            async for grid_out in cursor:
                files.append({
                    "id": grid_out._id,
                    "filename": grid_out.filename,
                    "metadata": grid_out.metadata,
                    "length": grid_out.length,
                    "upload_date": grid_out.upload_date
                })
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise

    async def update_metadata(self, 
                            file_id: ObjectId, 
                            metadata_updates: Dict[str, Any]) -> bool:
        """Update file metadata"""
        try:
            # Get existing metadata
            grid_out = await self.fs.open_download_stream(file_id)
            existing_metadata = grid_out.metadata or {}

            # Merge with updates
            updated_metadata = {
                **existing_metadata,
                **metadata_updates,
                "updated_at": datetime.utcnow()
            }

            # Update in files collection
            await self.db.fs.files.update_one(
                {"_id": file_id},
                {"$set": {"metadata": updated_metadata}}
            )

            logger.info(f"Successfully updated metadata for file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            return False

    async def cleanup_old_files(self, days: int = 30) -> int:
        """Clean up files older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await self.db.fs.files.delete_many({
                "uploadDate": {"$lt": cutoff_date},
                "metadata.persistent": {"$ne": True}  # Don't delete files marked as persistent
            })
            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise