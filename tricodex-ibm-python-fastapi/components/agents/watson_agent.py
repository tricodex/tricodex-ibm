"""
Process analysis agent using IBM Granite LLM
"""
import logging
from typing import Dict, Any
from langchain_ibm import WatsonxLLM
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class WatsonAgent(BaseAgent):
    """Process analysis agent using IBM Granite"""
    
    def __init__(self, llm: WatsonxLLM, timeout: int = 300):
        super().__init__(timeout)
        self.model = llm
        self._api_calls = 0
        self._last_call_time = 0
        logger.info("Watson LLM initialized successfully")
    
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with Watson"""
        try:
            prompt = self._create_analysis_prompt(data)
            response = await self._generate_response(prompt)
            
            # Process and structure the response
            analysis_result = self._process_analysis_results(response, data)
            
            return self._structure_output({
                "insights": analysis_result.get("insights", []),
                "patterns": analysis_result.get("patterns", []),
                "metrics": analysis_result.get("metrics", {}),
                "recommendations": analysis_result.get("recommendations", [])
            })
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Watson with safety checks"""
        try:
            self._api_calls += 1
            logger.info(f"Making Watson API call #{self._api_calls}")
            
            response = await self.model.agenerate([prompt])
            return response.generations[0][0].text
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Failed to generate Watson response: {e}")
            raise
    
    def _process_analysis_results(self, response: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure analysis results"""
        try:
            # Parse the response and extract structured information
            results = self._validate_json(response)
            
            return {
                "insights": results.get("insights", []),
                "patterns": results.get("patterns", []),
                "metrics": results.get("metrics", {}),
                "recommendations": results.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to process analysis results: {e}")
            return {}