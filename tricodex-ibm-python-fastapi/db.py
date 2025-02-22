"""
Database utilities for ProcessLens
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
import os
from datetime import datetime, timedelta
import ssl

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        try:
            # Configure SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create MongoDB client with SSL configuration
            cls.client = AsyncIOMotorClient(
                os.getenv("MONGODB_URL"),
                tls=True,
                tlsAllowInvalidCertificates=True,  # Only for development, remove in production
                ssl_cert_reqs=ssl.CERT_NONE  # Only for development, use proper cert validation in production
            )
            logger.info("Connected to MongoDB")
            
            # Create indexes for better query performance
            db = cls.client.processlens_db
            await db.analyses.create_index([("created_at", -1)])
            await db.analyses.create_index([("status", 1)])
            await db.analyses.create_index([("project.name", 1)])
            
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise e
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")
    
    @classmethod
    async def cleanup_old_analyses(cls, days: int = 30):
        """Clean up old analyses to manage storage"""
        if not cls.client:
            logger.error("Database not connected")
            return
            
        try:
            db = cls.client.processlens_db
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await db.analyses.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": {"$in": ["completed", "failed"]}
            })
            logger.info(f"Cleaned up {result.deleted_count} old analyses")
        except Exception as e:
            logger.error(f"Error cleaning up old analyses: {e}")
            raise e