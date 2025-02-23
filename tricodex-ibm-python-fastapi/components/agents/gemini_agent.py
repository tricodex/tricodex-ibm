"""
Process analysis agent using Google's Gemini model
"""
from typing import Dict, Any
import logging
from google import genai
from .base_agent import BaseAgent
import json

logger = logging.getLogger(__name__)

class GeminiAgent(BaseAgent):
    """Process analysis agent using Gemini"""
    
    def __init__(self, api_key: str, timeout: int = 300):
        super().__init__(timeout)
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
    
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with Gemini"""
        try:
            prompt = self._create_analysis_prompt(data)
            response = await self._generate_response(prompt)
            structured = self._structure_output(self._validate_json(response))
            
            # Add Gemini-specific language analysis
            if "metadata" in data:
                language_insights = await self._analyze_language_patterns(data["metadata"])
                structured["language_insights"] = language_insights
                
            return structured
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini with safety checks"""
        try:
            self._check_timeout()
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
            
        except Exception as e:
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
