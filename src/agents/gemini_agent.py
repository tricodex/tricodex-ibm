from typing import Dict, Any
import logging
from google import genai
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GeminiAgent:
    """Process analysis agent using Google's Gemini model"""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        self.start_time = None
        self.timeout = 300
        
    async def analyze_tickets(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ticket data using Gemini"""
        try:
            prompt = f"""Analyze this ticket system data and provide insights in JSON format:
            
            Metadata: {data['metadata']}
            Metrics: {data['metrics']}
            Patterns: {data['patterns']}
            Data Quality: {data['data_quality']}
            
            Include:
            1. Key insights about distribution and patterns
            2. Process bottlenecks and inefficiencies
            3. Improvement recommendations
            4. Data quality impact
            5. Language considerations
            """
            
            response = await self._generate_response(prompt)
            return self._structure_insights(response)
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": ["Check data completeness", "Verify input format"]
            }

    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini with timeout handling"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    def _structure_insights(self, response: str) -> Dict[str, Any]:
        """Convert Gemini response to structured format"""
        try:
            # Initialize structure
            structured = {
                "insights": [],
                "bottlenecks": [],
                "recommendations": [],
                "data_quality_impact": {},
                "language_considerations": {}
            }
            
            # Parse JSON response
            try:
                data = json.loads(response)
                
                # Extract insights
                if "insights" in data:
                    structured["insights"] = data["insights"]
                    
                # Extract bottlenecks
                if "bottlenecks" in data:
                    structured["bottlenecks"] = data["bottlenecks"]
                    
                # Extract recommendations
                if "recommendations" in data:
                    structured["recommendations"] = data["recommendations"]
                    
                # Extract data quality impact
                if "data_quality_impact" in data:
                    structured["data_quality_impact"] = data["data_quality_impact"]
                    
                # Extract language considerations
                if "language_considerations" in data:
                    structured["language_considerations"] = data["language_considerations"]
                    
            except json.JSONDecodeError:
                # If response is not JSON, attempt to parse structured text
                sections = response.split("\n\n")
                for section in sections:
                    if "insights:" in section.lower():
                        structured["insights"] = [i.strip() for i in section.split("\n")[1:] if i.strip()]
                    elif "bottlenecks:" in section.lower():
                        structured["bottlenecks"] = [b.strip() for b in section.split("\n")[1:] if b.strip()]
                    elif "recommendations:" in section.lower():
                        structured["recommendations"] = [r.strip() for r in section.split("\n")[1:] if r.strip()]
            
            return structured
            
        except Exception as e:
            logger.error(f"Failed to structure Gemini insights: {e}")
            raise
