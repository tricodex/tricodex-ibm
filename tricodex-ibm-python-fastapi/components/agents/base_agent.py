"""
Base agent class for all LLM agents
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
import json
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.start_time: Optional[datetime] = None
        self._reset_state()
    
    def _reset_state(self) -> None:
        """Reset agent state"""
        self.start_time = None
        self.current_state = "init"
        self.analysis_results = {}
        self._error_count = 0
        self._last_error = None
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis entry point with timeout handling"""
        try:
            self.start_time = datetime.now()
            self._validate_input_data(data)
            sanitized_data = self._sanitize_data(data)
            
            # Execute analysis with progress tracking
            result = await self._run_analysis(sanitized_data)
            
            # Validate output structure
            self._validate_output_structure(result)
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            return {
                "status": "error",
                "error": str(e),
                "error_count": self._error_count,
                "partial_results": self.analysis_results,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            self._reset_state()
    
    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        """Validate input data structure"""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict input, got {type(data)}")
            
        required_fields = {"metadata", "metrics"}
        missing = required_fields - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
    
    def _validate_output_structure(self, output: Dict[str, Any]) -> None:
        """Validate output structure"""
        required_fields = {"status", "insights", "patterns", "metrics"}
        if not all(field in output for field in required_fields):
            logger.error(f"Invalid output structure: {output.keys()}")
            raise ValueError("Output missing required fields")
    
    def _sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data"""
        if isinstance(data, dict):
            return {str(k): self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, (pd.Timestamp, datetime)):
            return data.isoformat()
        elif pd.isna(data) or (isinstance(data, float) and pd.isna(data)):
            return None
        elif hasattr(data, 'to_dict'):
            return self._sanitize_data(data.to_dict())
        elif hasattr(data, 'item'):
            return data.item()
        return data
    
    @abstractmethod
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement specific analysis logic in subclasses"""
        pass
    
    def _check_timeout(self) -> None:
        """Check if analysis has exceeded timeout"""
        if not self.start_time:
            return
            
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed > self.timeout:
            raise TimeoutError(f"Analysis timeout after {self.timeout} seconds")
    
    def _structure_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure consistent output structure"""
        try:
            sanitized_output = self._sanitize_data(output)
            structured = {
                "status": "success",
                "insights": sanitized_output.get("insights", []),
                "patterns": sanitized_output.get("patterns", []),
                "recommendations": sanitized_output.get("recommendations", []),
                "metrics": sanitized_output.get("metrics", {}),
                "data_quality": sanitized_output.get("data_quality", {}),
                "synthesis": sanitized_output.get("synthesis", {}),
                "timestamp": datetime.now().isoformat(),
                "processing_time": self._get_processing_time()
            }
            
            # Add error information if any occurred
            if self._error_count > 0:
                structured["warnings"] = {
                    "error_count": self._error_count,
                    "last_error": self._last_error
                }
                
            return structured
            
        except Exception as e:
            logger.error(f"Failed to structure output: {e}")
            raise
    
    def _get_processing_time(self) -> float:
        """Calculate total processing time"""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    @staticmethod
    def _validate_json(text: str) -> Dict[str, Any]:
        """Safely parse JSON from text"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Attempt to extract JSON-like structure from text
            sections = {}
            current_section = None
            current_items = []
            
            for line in text.split("\n"):
                if ":" in line and not line.strip().startswith("-"):
                    if current_section and current_items:
                        sections[current_section] = current_items
                    current_section = line.split(":")[0].strip().lower()
                    current_items = []
                elif line.strip().startswith("-"):
                    current_items.append(line.strip("- ").strip())
            
            if current_section and current_items:
                sections[current_section] = current_items
                
            return sections