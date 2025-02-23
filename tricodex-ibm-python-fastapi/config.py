"""
Centralized configuration for ProcessLens
"""
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Model configurations
    WATSON_CONFIG = {
        "model_id": "ibm/granite-3-8b-instruct",
        "apikey": os.getenv("IBM_API_KEY"),
        "project_id": os.getenv("PROJECT_ID"),
        "url": os.getenv("WATSONX_URL")
    }
    
    GEMINI_CONFIG = {
        "api_key": os.getenv("GOOGLE_API_KEY")
    }
    
    # Database configurations
    MONGODB_URL = os.getenv("MONGODB_URL")
    DB_NAME = "processlens_db"
    
    # Analysis configurations
    DEFAULT_TIMEOUT = 300
    CHUNK_SIZE = 1024 * 1024  # 1MB
    
    # API configurations
    CORS_ORIGINS = ["http://localhost:3000"]
    
    # WebSocket configurations
    WS_PING_INTERVAL = 30  # seconds
    WS_RETRY_INTERVALS = [1000, 2000, 3000, 5000, 8000]  # milliseconds
    
    @classmethod
    def get_model_config(cls, model_type: str) -> Dict[str, Any]:
        """Get model configuration based on type"""
        if model_type == "watson":
            return cls.WATSON_CONFIG
        elif model_type == "gemini":
            return cls.GEMINI_CONFIG
        else:
            raise ValueError(f"Unknown model type: {model_type}")