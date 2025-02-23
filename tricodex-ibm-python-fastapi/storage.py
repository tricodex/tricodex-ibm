"""
Enhanced GridFS storage implementation for ProcessLens
"""
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from bson import ObjectId
import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

class GridFSStorage:
    def __init__(self, db):
        """Initialize GridFS storage with MongoDB database"""
        self.db = db
        self.fs = AsyncIOMotorGridFSBucket(
            db,
            chunk_size_bytes=1024 * 1024  # 1MB chunks
        )

    async def save_file(self, 
                       file_content: bytes | BinaryIO, 
                       filename: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> ObjectId:
        """Save file to GridFS with metadata"""
        try:
            metadata = metadata or {}
            metadata['upload_date'] = datetime.utcnow()
            
            if isinstance(file_content, bytes):
                file_content = io.BytesIO(file_content)
            
            file_id = await self.fs.upload_from_stream(
                filename=filename,
                source=file_content,
                metadata=metadata
            )
            logger.info(f"File saved successfully: {filename}")
            return file_id

        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise

    async def get_file(self, file_id: ObjectId) -> bytes:
        """Retrieve file from GridFS by ID"""
        try:
            buffer = io.BytesIO()
            await self.fs.download_to_stream(file_id, buffer)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to retrieve file {file_id}: {e}")
            raise

    async def get_dataframe(self, file_id: ObjectId) -> pd.DataFrame:
        """Retrieve file from GridFS and convert to pandas DataFrame"""
        try:
            content = await self.get_file(file_id)
            metadata = await self.get_metadata(file_id)
            file_type = metadata.get('content_type', '').lower()
            
            if 'csv' in file_type:
                return pd.read_csv(io.BytesIO(content))
            elif 'excel' in file_type or 'xlsx' in file_type:
                return pd.read_excel(io.BytesIO(content))
            else:
                # Default to CSV with multiple encodings
                for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                    try:
                        return pd.read_csv(io.BytesIO(content), encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                raise ValueError("Unable to decode file with supported encodings")

        except Exception as e:
            logger.error(f"Failed to convert file {file_id} to DataFrame: {e}")
            raise

    async def get_metadata(self, file_id: ObjectId) -> Dict[str, Any]:
        """Get file metadata from GridFS"""
        try:
            grid_out = await self.fs.open_download_stream(file_id)
            return grid_out.metadata or {}

        except Exception as e:
            logger.error(f"Failed to get metadata for file {file_id}: {e}")
            raise

    async def delete_file(self, file_id: ObjectId) -> bool:
        """Delete file from GridFS"""
        try:
            await self.fs.delete(file_id)
            logger.info(f"File {file_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def list_files(self, 
                        filter_dict: Optional[Dict[str, Any]] = None, 
                        skip: int = 0, 
                        limit: int = 100) -> list:
        """List files in GridFS with optional filtering"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.fs.find(
                filter=filter_dict,
                skip=skip,
                limit=limit,
                no_cursor_timeout=True
            )
            
            files = []
            async for grid_out in cursor:
                files.append({
                    'id': str(grid_out._id),
                    'filename': grid_out.filename,
                    'length': grid_out.length,
                    'upload_date': grid_out.upload_date,
                    'metadata': grid_out.metadata
                })
            return files

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise

    async def update_metadata(self, 
                            file_id: ObjectId, 
                            metadata_updates: Dict[str, Any]) -> bool:
        """Update file metadata"""
        try:
            current_metadata = await self.get_metadata(file_id)
            updated_metadata = {**current_metadata, **metadata_updates}
            
            await self.db.fs.files.update_one(
                {'_id': file_id},
                {'$set': {'metadata': updated_metadata}}
            )
            logger.info(f"Metadata updated for file {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update metadata for file {file_id}: {e}")
            return False

    async def cleanup_old_files(self, days: int = 30) -> int:
        """Clean up files older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await self.db.fs.files.delete_many({
                'uploadDate': {'$lt': cutoff_date}
            })
            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} files older than {days} days")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            raise