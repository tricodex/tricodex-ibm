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
import pandas as pd
import io
import csv

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

def validate_file_content(content: bytes, filename: str) -> None:
    """
    Validate file content for analysis
    
    Args:
        content: Raw file content bytes
        filename: Original filename for type detection
    
    Raises:
        ValidationError: If file content is invalid
    """
    if not content:
        raise ValidationError("Empty file content")
        
    # Determine file type from extension
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    try:
        if ext == 'csv':
            # Try parsing as CSV
            try:
                pd.read_csv(io.BytesIO(content), nrows=5)
            except Exception as e:
                raise ValidationError(
                    "Invalid CSV format",
                    {"error": str(e)}
                )
                
            # Validate CSV structure
            csv_reader = csv.reader(io.StringIO(content.decode('utf-8')))
            headers = next(csv_reader, None)
            if not headers:
                raise ValidationError("CSV file must have headers")
                
            # Check for minimum required columns for analysis
            min_cols = 2  # At least 2 columns needed for meaningful analysis
            if len(headers) < min_cols:
                raise ValidationError(
                    f"CSV must have at least {min_cols} columns",
                    {"found": len(headers)}
                )
                
        elif ext in ['xls', 'xlsx']:
            # Try parsing as Excel
            try:
                pd.read_excel(io.BytesIO(content), nrows=5)
            except Exception as e:
                raise ValidationError(
                    "Invalid Excel format",
                    {"error": str(e)}
                )
                
        elif ext == 'json':
            # Try parsing as JSON
            try:
                data = json.loads(content)
                if not isinstance(data, (list, dict)):
                    raise ValidationError(
                        "JSON content must be an array or object"
                    )
            except json.JSONDecodeError as e:
                raise ValidationError(
                    "Invalid JSON format",
                    {"error": str(e)}
                )
                
        else:
            raise ValidationError(
                f"Unsupported file type: {ext}",
                {"supported": ['csv', 'xls', 'xlsx', 'json']}
            )
            
        # Size validation (100MB limit)
        max_size = 100 * 1024 * 1024  # 100MB
        if len(content) > max_size:
            raise ValidationError(
                "File too large",
                {
                    "max_size_mb": max_size // (1024 * 1024),
                    "file_size_mb": len(content) // (1024 * 1024)
                }
            )
            
    except UnicodeDecodeError:
        raise ValidationError("File must be UTF-8 encoded")
    except Exception as e:
        if not isinstance(e, ValidationError):
            logger.error(f"Unexpected validation error: {e}")
            raise ValidationError(
                "File validation failed",
                {"error": str(e)}
            )
        raise