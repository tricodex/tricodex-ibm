"""
Centralized configuration for ProcessLens
"""
from typing import Dict, Any, Optional, Tuple
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Configuration management for ProcessLens"""
    
    # Model configurations with validation
    # In config.py, update WATSON_CONFIG

    WATSON_CONFIG = {
        "model_id": "ibm/granite-3-8b-instruct",  # Updated to supported model
        "api_key": os.getenv("IBM_API_KEY"),
        "project_id": os.getenv("PROJECT_ID"),
        "url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    }
    
    GEMINI_CONFIG = {
        "api_key": os.getenv("GOOGLE_API_KEY"),
        "model": "gemini-2.0-flash",  # Using latest flash model
        "params": {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048
        }
    }
    
    # Database configurations
    MONGODB_URL = os.getenv("MONGODB_URL")
    DB_NAME = "processlens_db"
    DB_CONFIG = {
        "tls": True,
        "retryWrites": True,
        "w": "majority"
    }
    
    # Analysis configurations
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "300"))
    CHUNK_SIZE = 1024 * 1024  # 1MB
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # API configurations
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    API_VERSION = "2.0.0"
    
    # WebSocket configurations
    WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "30"))
    WS_RETRY_INTERVALS = [1000, 2000, 3000, 5000, 8000]  # milliseconds
    
    @classmethod
    def validate_config(cls) -> Tuple[bool, Optional[str]]:
        """Validate all required configuration"""
        missing = []
        
        # Validate Watson config
        watson_keys = ["IBM_API_KEY", "PROJECT_ID", "WATSONX_URL"]
        for key in watson_keys:
            if not os.getenv(key):
                missing.append(key)
                logger.error(f"Missing required Watson configuration: {key}")
        
        # Validate Gemini config
        if not os.getenv("GOOGLE_API_KEY"):
            missing.append("GOOGLE_API_KEY")
            logger.error("Missing required Gemini API key")
        
        # Validate MongoDB config
        if not os.getenv("MONGODB_URL"):
            missing.append("MONGODB_URL")
            logger.error("Missing required MongoDB URL")
        
        # Check other critical configurations
        if not cls.CORS_ORIGINS:
            missing.append("CORS_ORIGINS")
            logger.error("No CORS origins configured")
            
        if not cls.DEFAULT_TIMEOUT > 0:
            missing.append("DEFAULT_TIMEOUT")
            logger.error("Invalid DEFAULT_TIMEOUT value")
        
        if missing:
            return False, f"Missing required environment variables: {', '.join(missing)}"
        
        logger.info("Configuration validation completed successfully")
        return True, None

    @classmethod
    def get_model_config(cls, model_type: str) -> Dict[str, Any]:
        """Get model configuration based on type with validation"""
        try:
            if model_type == "watson":
                config = cls.WATSON_CONFIG
                if not all(v for k, v in config.items() if k in ["api_key", "project_id", "url"]):
                    raise ValueError("Invalid Watson configuration - missing required values")
                return config
                
            elif model_type == "gemini":
                config = cls.GEMINI_CONFIG
                if not config["api_key"]:
                    raise ValueError("Invalid Gemini configuration - missing API key")
                return config
                
            elif model_type == "function":
                # Function agent uses Watson config
                return cls.WATSON_CONFIG
                
            else:
                raise ValueError(f"Unknown model type: {model_type}")
                
        except Exception as e:
            logger.error(f"Error getting model config for {model_type}: {e}")
            raise
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": cls.MONGODB_URL,
            "db_name": cls.DB_NAME,
            **cls.DB_CONFIG
        }
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "cors_origins": cls.CORS_ORIGINS,
            "version": cls.API_VERSION,
            "timeout": cls.DEFAULT_TIMEOUT
        }