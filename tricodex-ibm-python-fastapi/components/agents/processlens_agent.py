"""
Process analysis agent using IBM Granite LLM
"""
import json
from typing import Dict, Any, List
import logging
import time
import asyncio
from langchain_ibm import WatsonxLLM
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ProcessLensAgent(BaseAgent):
    """Process analysis agent using IBM Granite"""
    
    def __init__(self, llm: WatsonxLLM, tools: List[Any], timeout: int = 300):
        super().__init__(timeout)
        self.llm = llm
        self.tools = tools
        self._api_calls = 0
        self._last_call_time = 0
        self.MAX_API_CALLS = 3  # Limit total API calls per analysis
    
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with IBM Granite using batched prompts"""
        start_time = time.time()
        logger.info("Starting WatsonX analysis")
        
        try:
            if self._api_calls >= self.MAX_API_CALLS:
                raise Exception("Maximum API calls exceeded")

            # Batch all analysis into a single comprehensive prompt
            prompt = self._create_batched_analysis_prompt(data)
            logger.debug(f"Generated batched prompt length: {len(prompt)}")
            
            # Single API call for main analysis
            self._api_calls += 1
            response = await self._generate_response(prompt)
            main_analysis = self._validate_json(response)
            
            # Optional: One additional call for metrics if needed
            metrics = None
            if "metrics" in data and self._api_calls < self.MAX_API_CALLS:
                metrics = await self._analyze_metrics(data["metrics"])
            
            execution_time = time.time() - start_time
            logger.info(f"WatsonX analysis completed in {execution_time:.2f}s with {self._api_calls} API calls")
            
            return self._structure_output({
                "analysis": main_analysis,
                "metrics": metrics or {}
            })
            
        except Exception as e:
            logger.error(f"WatsonX analysis failed after {time.time() - start_time:.2f}s: {e}")
            raise

    def _create_batched_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create a comprehensive single prompt for analysis"""
        return f"""Analyze this process data and provide a complete analysis in a single response:

        Data Summary:
        {json.dumps(data.get('metadata', {}), indent=2)}
        
        Process Metrics:
        {json.dumps(data.get('metrics', {}), indent=2)}
        
        Analysis Requirements:
        1. Key Performance Indicators (KPIs)
        2. Process Patterns and Anomalies
        3. Efficiency Analysis
        4. Resource Utilization
        5. Bottleneck Identification
        6. Improvement Recommendations
        
        Return a single comprehensive JSON response with all analyses combined.
        Include confidence scores for each insight.
        Ensure all numeric metrics have clear units and context.
        """

    async def _analyze_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Focused metrics analysis with single API call"""
        try:
            if self._api_calls >= self.MAX_API_CALLS:
                return {}
                
            prompt = f"""Analyze these specific metrics and provide detailed insights:
            {json.dumps(metrics, indent=2)}
            Focus on:
            1. Statistical significance
            2. Trend identification
            3. Performance benchmarking
            Return analysis in JSON format with confidence scores.
            """
            
            self._api_calls += 1
            response = await self._generate_response(prompt)
            return self._validate_json(response)
            
        except Exception as e:
            logger.error(f"Metrics analysis failed: {e}")
            return {}

    async def _generate_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response from WatsonX with rate limiting"""
        try:
            self._check_timeout()
            
            # Rate limiting
            current_time = time.time()
            if self._last_call_time:
                time_since_last = current_time - self._last_call_time
                if time_since_last < 1.0:
                    await asyncio.sleep(1.0 - time_since_last)
            
            logger.info(f"Making WatsonX API call #{self._api_calls}")
            start_time = time.time()
            
            response = await self.llm.agenerate(prompt)
            
            self._last_call_time = time.time()
            execution_time = self._last_call_time - start_time
            
            logger.debug(f"WatsonX API call completed in {execution_time:.2f}s")
            return self._validate_json(response)
            
        except Exception as e:
            logger.error(f"WatsonX generation failed: {e}")
            raise
