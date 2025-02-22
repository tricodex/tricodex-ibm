"""
Database utilities for ProcessLens
"""
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional
from pymongo.errors import PyMongoError, ConnectionFailure
import logging
import os
from datetime import datetime, timedelta
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None  # Store database instance
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        try:
            # Create MongoDB client with modern configuration
            cls.client = AsyncIOMotorClient(
                os.getenv("MONGODB_URL"),
                server_api=ServerApi('1'),
                tls=True,
                tlsCAFile=certifi.where()
            )
            
            # Test connection with ping
            try:
                await cls.client.admin.command('ping')
                logger.info("Connected to MongoDB")
            except ConnectionFailure as cf:
                logger.error(f"Failed to ping MongoDB server: {cf}")
                raise
            
            # Initialize database instance
            cls.db = cls.client.processlens_db
            
            # Create indexes with error handling
            try:
                await cls.db.analyses.create_index([("created_at", -1)])
                await cls.db.analyses.create_index([("status", 1)])
                await cls.db.analyses.create_index([("project.name", 1)])
            except PyMongoError as e:
                logger.warning(f"Error creating indexes: {e}")
                # Continue even if index creation fails as they're not critical
            
            return cls.db
            
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            try:
                cls.client.close()
                cls.db = None
                logger.info("Closed MongoDB connection")
            except PyMongoError as e:
                logger.error(f"Error closing MongoDB connection: {e}")
                raise
    
    @classmethod
    async def get_db(cls):
        """Get database instance, connecting if necessary"""
        if cls.db is None:
            await cls.connect_db()
        return cls.db
    
    @classmethod
    async def cleanup_old_analyses(cls, days: int = 30):
        """Clean up old analyses to manage storage"""
        if not cls.db:
            logger.error("Database not connected")
            return
            
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await cls.db.analyses.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": {"$in": ["completed", "failed"]}
            })
            
            if result:
                deleted_count = result.deleted_count
                logger.info(f"Cleaned up {deleted_count} old analyses")
                return {"deleted_count": deleted_count}
            else:
                logger.warning("Cleanup operation returned no result")
                return {"deleted_count": 0}
                
        except PyMongoError as e:
            logger.error(f"MongoDB error during cleanup: {e}")
            raise
        except Exception as e:
            logger.error(f"Error cleaning up old analyses: {e}")
            raise