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
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis entry point with timeout handling"""
        try:
            self.start_time = datetime.now()
            sanitized_data = self._sanitize_data(data)
            return await self._run_analysis(sanitized_data)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "partial_results": self.analysis_results
            }
        finally:
            self._reset_state()
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize data to handle timestamps and other special types"""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, (pd.Timestamp, datetime)):
            return data.isoformat()
        elif pd.isna(data):  # Handle NaN/None values
            return None
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
        sanitized_output = self._sanitize_data(output)
        return {
            "insights": sanitized_output.get("insights", []),
            "patterns": sanitized_output.get("patterns", []),
            "recommendations": sanitized_output.get("recommendations", []),
            "metrics": sanitized_output.get("metrics", {}),
            "data_quality": sanitized_output.get("data_quality", {})
        }
    
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