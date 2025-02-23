"""
ProcessLens: Universal Process Mining Framework
Core implementation using RAR (Retrieval-Augmented Reasoning) with IBM Granite
"""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import pandas as pd
from components.agents.factory import AgentFactory
from components.pipeline.analysis_pipeline import EnhancedAnalysisPipeline
from config import Config
from utils.helpers import ProcessLensError, async_retry, validate_json_response
from utils.logging_config import setup_logging

logger = setup_logging()

@dataclass
class ProcessStep:
    """Process step with timing and resource information"""
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    resources: List[str] = None
    status: str = "pending"
    metrics: Dict[str, Any] = None

@dataclass
class ProcessPattern:
    """Detected process pattern with context"""
    pattern_type: str
    confidence: float
    context: Dict[str, Any]
    impact: Dict[str, float]
    recommendations: List[str]

class ProcessLens:
    """Core ProcessLens implementation"""
    
    def __init__(self):
        """Initialize ProcessLens with agents and pipeline"""
        # Initialize agents using factory
        self.watson_agent = AgentFactory.create_agent("watson")
        self.gemini_agent = AgentFactory.create_agent("gemini")
        self.function_agent = AgentFactory.create_agent("function")
        
        # Initialize analysis pipeline
        self.pipeline = EnhancedAnalysisPipeline(
            watson_agent=self.watson_agent,
            gemini_agent=self.gemini_agent,
            cache_ttl=30  # 30 minutes cache
        )
        
        logger.info("ProcessLens initialized successfully")
    
    @async_retry(retries=3, delay=1.0)
    async def analyze_dataset(self, 
                            df_data: Union[str, pd.DataFrame],
                            cache_key: Optional[str] = None,
                            business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a dataset with both Watson and Gemini models
        
        Args:
            df_data: DataFrame or path to dataset
            cache_key: Optional cache key for results
            business_context: Optional business context for enhanced analysis
        
        Returns:
            Dict containing analysis results from both models
            
        Raises:
            ProcessLensError: If analysis fails or input is invalid
        """
        try:
            # Input validation
            df = self._validate_and_load_data(df_data)
            
            # Run enhanced analysis pipeline
            results = await self.pipeline.analyze_dataset(
                df=df,
                cache_key=cache_key
            )
            
            # Add business context if provided
            if business_context:
                results["business_context"] = await self._analyze_business_context(
                    business_context,
                    results
                )
            
            # Add function-based analysis if needed
            if results.get("metrics"):
                function_results = await self._analyze_with_functions(
                    results["metrics"],
                    business_context
                )
                results["function_analysis"] = function_results
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise ProcessLensError(f"Analysis failed: {str(e)}")
    
    def _validate_and_load_data(self, df_data: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """Validate and load input data"""
        try:
            # Convert to DataFrame if needed
            if isinstance(df_data, str):
                df = pd.read_csv(df_data)
            else:
                df = df_data
                
            # Validation
            if not isinstance(df, pd.DataFrame):
                raise ProcessLensError("Input must be a DataFrame or path to CSV")
                
            if df.empty:
                raise ProcessLensError("Empty dataset provided")
                
            return df
            
        except Exception as e:
            raise ProcessLensError(f"Data validation failed: {str(e)}")
    
    async def _analyze_business_context(self,
                                      context: Dict[str, Any],
                                      results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business context impact on results"""
        try:
            # Validate context
            if not isinstance(context, dict):
                raise ProcessLensError("Business context must be a dictionary")
                
            # Prepare context analysis prompt
            prompt = f"""
            Analyze these results in the given business context:
            
            Business Context:
            {json.dumps(context, indent=2)}
            
            Analysis Results:
            {json.dumps(results, indent=2)}
            
            Focus on:
            1. Business impact of identified patterns
            2. Cost implications
            3. Strategic recommendations
            4. Risk assessment
            
            Return analysis in JSON format.
            """
            
            # Use Watson agent for business context analysis
            context_analysis = await self.watson_agent.analyze({
                "prompt": prompt,
                "context": context,
                "results": results
            })
            
            # Validate and structure response
            return {
                "impact_analysis": context_analysis.get("insights", []),
                "strategic_recommendations": context_analysis.get("recommendations", []),
                "risk_assessment": context_analysis.get("metrics", {}),
                "confidence": context_analysis.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.warning(f"Business context analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_with_functions(self,
                                    metrics: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze data using function calling capabilities"""
        try:
            # Validate metrics
            if not isinstance(metrics, dict):
                raise ProcessLensError("Metrics must be a dictionary")
                
            # Create analysis payload
            payload = {
                "metrics": metrics,
                "time_period": "all",  # Default to all data
                "target_goals": context.get("goals", {}) if context else {}
            }
            
            # Use function calling agent
            results = await self.function_agent.analyze(payload)
            
            # Validate and structure response
            return {
                "kpi_analysis": results.get("metrics_analysis", {}),
                "efficiency_metrics": results.get("efficiency_metrics", {}),
                "function_insights": results.get("insights", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Function analysis failed: {e}")
            return {"error": str(e)}