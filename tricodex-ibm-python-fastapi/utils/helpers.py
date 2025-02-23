"""
Common utilities for ProcessLens
"""
from typing import Dict, Any, Optional, TypeVar, Callable
from functools import wraps
import asyncio
import traceback
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ProcessLensError(Exception):
    """Base exception class for ProcessLens"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

class ValidationError(ProcessLensError):
    """Validation error in data processing"""
    pass

class ModelError(ProcessLensError):
    """Error in model inference"""
    pass

def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Retry decorator for async functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {retries} attempts failed. "
                            f"Last error: {str(e)}"
                        )
                        
            raise last_exception

        return wrapper
    return decorator

def validate_json_response(response: str) -> Dict[str, Any]:
    """Validate and extract JSON from model response"""
    try:
        # Try direct JSON parsing first
        return json.loads(response)
    except json.JSONDecodeError:
        # Attempt to extract JSON from text
        import re
        json_pattern = r'\{(?:[^{}]|(?R))*\}'
        matches = re.finditer(json_pattern, response)
        
        for match in matches:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
                
        raise ValidationError(
            "Failed to extract valid JSON from response",
            {"response": response}
        )

def format_error_response(error: Exception) -> Dict[str, Any]:
    """Format exception for API response"""
    if isinstance(error, ProcessLensError):
        return {
            "status": "error",
            "message": str(error),
            "details": error.details,
            "timestamp": error.timestamp,
            "type": error.__class__.__name__
        }
    else:
        return {
            "status": "error",
            "message": str(error),
            "details": {
                "traceback": traceback.format_exc()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "type": "UnhandledError"
        }

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize data for safe storage and transmission"""
    def _sanitize_value(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [_sanitize_value(v) for v in value]
        elif isinstance(value, dict):
            return {str(k): _sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, datetime):
            return value.isoformat()
        else:
            return str(value)
            
    return {str(k): _sanitize_value(v) for k, v in data.items()}