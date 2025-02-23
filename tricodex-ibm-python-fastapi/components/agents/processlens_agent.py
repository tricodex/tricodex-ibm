"""
Process analysis agent using IBM Granite LLM
"""
import json
from typing import Dict, Any, List
import logging
from langchain_ibm import WatsonxLLM
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ProcessLensAgent(BaseAgent):
    """Process analysis agent using IBM Granite"""
    
    def __init__(self, llm: WatsonxLLM, tools: List[Any], timeout: int = 300):
        super().__init__(timeout)
        self.llm = llm
        self.tools = tools
    
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with IBM Granite"""
        prompt = self._create_analysis_prompt(data)
        
        try:
            response = await self.llm.agenerate(prompt)
            structured = self._structure_output(self._validate_json(response))
            
            # Add model-specific metrics
            if "metrics" in data:
                enhanced_metrics = await self._enhance_metrics(data["metrics"])
                structured["enhanced_metrics"] = enhanced_metrics
                
            return structured
            
        except Exception as e:
            logger.error(f"IBM Granite analysis failed: {e}")
            raise
    
    async def _enhance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Add IBM-specific metric enhancements"""
        try:
            prompt = f"""
            Analyze these process metrics and provide advanced insights:
            {json.dumps(metrics, indent=2)}
            Focus on:
            1. Performance bottlenecks
            2. Optimization opportunities
            3. Resource utilization
            4. Business impact
            
            Return a JSON structure with detailed analysis.
            """
            
            response = await self.llm.agenerate(prompt)
            return self._validate_json(response)
            
        except Exception as e:
            logger.warning(f"Metric enhancement failed: {e}")
            return metrics
    
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
        1. Key insights about distribution and patterns
        2. Process bottlenecks and inefficiencies
        3. Recommendations for improvement
        4. Data quality impact
        5. Resource optimization suggestions
        
        Return analysis in JSON format.
        """
