"""
Process analysis agent using Google's Gemini model
"""
import asyncio
from typing import Dict, Any
import logging
from google import genai
from .base_agent import BaseAgent
import json
import time

logger = logging.getLogger(__name__)

class GeminiAgent(BaseAgent):
    """Process analysis agent using Gemini"""
    
    def __init__(self, config: Dict[str, Any], timeout: int = 300):
        super().__init__(timeout)
        if not config.get("api_key"):
            raise ValueError("Gemini API key is required")
        
        # Initialize Gemini
        genai.configure(api_key=config["api_key"])
        self.model = genai.GenerativeModel(
            model_name=config.get("model", "gemini-2.0-flash"),
            generation_config=config.get("params", {})
        )
        self._api_calls = 0
        self._last_call_time = 0
    
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with Gemini"""
        try:
            logger.info("Starting Gemini analysis")
            start_time = time.time()
            
            prompt = self._create_analysis_prompt(data)
            logger.debug(f"Generated prompt length: {len(prompt)}")
            
            response = await self._generate_response(prompt)
            structured = self._structure_output(self._validate_json(response))
            
            # Add Gemini-specific language analysis
            if "metadata" in data:
                logger.info("Running language pattern analysis")
                language_insights = await self._analyze_language_patterns(data["metadata"])
                structured["language_insights"] = language_insights
            
            execution_time = time.time() - start_time
            logger.info(f"Gemini analysis completed in {execution_time:.2f}s with {self._api_calls} API calls")
            
            return structured
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini with safety checks"""
        try:
            self._check_timeout()
            self._api_calls += 1
            
            # Rate limiting
            current_time = time.time()
            if self._last_call_time:
                time_since_last = current_time - self._last_call_time
                if time_since_last < 1.0:
                    await asyncio.sleep(1.0 - time_since_last)
            
            logger.info(f"Making Gemini API call #{self._api_calls}")
            start_time = time.time()
            
            # Use async generation
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            self._last_call_time = time.time()
            execution_time = self._last_call_time - start_time
            
            logger.debug(f"Gemini API call completed in {execution_time:.2f}s")
            
            # Handle response based on new API
            if hasattr(response, 'text'):
                return response.text
            return str(response)
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def _analyze_language_patterns(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze language patterns in the data"""
        if not metadata.get("languages"):
            return {}
            
        try:
            prompt = f"""
            Analyze language patterns in this metadata:
            {json.dumps(metadata, indent=2)}
            Focus on:
            1. Language distribution
            2. Regional patterns
            3. Translation needs
            4. Cultural considerations
            
            Return a JSON structure with insights.
            """
            
            response = await self._generate_response(prompt)
            return self._validate_json(response)
            
        except Exception as e:
            logger.warning(f"Language analysis failed: {e}")
            return {}
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create structured analysis prompt"""
        return f"""Analyze this process data and provide insights:

        Metadata:
        {json.dumps(data.get('metadata', {}), indent=2)}
        
        Metrics:
        {json.dumps(data.get('metrics', {}), indent=2)}
        
        Patterns:
        {json.dumps(data.get('patterns', []), indent=2)}
        
        Data Quality:
        {json.dumps(data.get('data_quality', {}), indent=2)}
        
        Provide detailed analysis including:
        1. Key insights and patterns
        2. Process bottlenecks
        3. Improvement recommendations
        4. Data quality impact
        5. Language and regional considerations
        
        Return analysis in JSON format.
        """
