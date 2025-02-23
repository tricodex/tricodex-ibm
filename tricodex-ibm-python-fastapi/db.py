"""
Database utilities for ProcessLens
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Dict, Any
from pymongo.server_api import ServerApi
from pymongo.errors import ServerSelectionTimeoutError
import logging
import os
import certifi
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls, max_retries: int = 3, retry_delay: int = 5) -> AsyncIOMotorDatabase:
        """Connect to MongoDB with retry logic"""
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                mongodb_url = os.getenv("MONGODB_URL")
                # Initialize the client with minimal required options for Atlas
                cls.client = AsyncIOMotorClient(
                    mongodb_url,
                    server_api=ServerApi('1'),
                    tls=True,
                    tlsCAFile=certifi.where(),
                )
                
                # Test connection
                await cls.client.admin.command('ping')
                logger.info("MongoDB connected successfully")
                
                cls.db = cls.client.processlens_db
                await cls._ensure_indexes()
                
                return cls.db
                
            except ServerSelectionTimeoutError as e:
                last_error = e
                retries += 1
                if retries < max_retries:
                    logger.warning(f"MongoDB connection attempt {retries} failed, retrying in {retry_delay} seconds... Error: {str(e)}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"MongoDB connection failed after {max_retries} attempts. URL: {mongodb_url.replace(mongodb_url.split('@')[0], '***')} Error: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"MongoDB connection failed: {e}")
                raise
    
    @classmethod
    async def _ensure_indexes(cls) -> None:
        """Create necessary database indexes"""
        try:
            if cls.db is not None:  # Changed from 'if not cls.db' to proper None check
                await cls.db.analyses.create_index([("created_at", -1)])
                await cls.db.analyses.create_index([("status", 1)])
                await cls.db.analyses.create_index([("project.name", 1)])
            else:
                logger.warning("Database not initialized, skipping index creation")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    @classmethod
    async def close_db(cls) -> None:
        """Close MongoDB connection"""
        if cls.client is not None:  # Changed from 'if cls.client' to proper None check
            cls.client.close()
            cls.db = None
            logger.info("MongoDB connection closed")
    
    @classmethod
    async def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance, connecting if necessary"""
        if cls.db is None:  # Changed from 'if cls.db is None' to proper None check
            await cls.connect_db()
        return cls.db
    
    @classmethod
    async def cleanup_old_analyses(cls, days: int = 30) -> Dict[str, int]:
        """Clean up old analyses"""
        if cls.db is None:  # Changed from 'if not cls.db' to proper None check
            return {"deleted_count": 0}
            
        try:
            result = await cls.db.analyses.delete_many({
                "created_at": {"$lt": datetime.utcnow() - timedelta(days=days)},
                "status": {"$in": ["completed", "failed"]}
            })
            return {"deleted_count": result.deleted_count if result else 0}
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise