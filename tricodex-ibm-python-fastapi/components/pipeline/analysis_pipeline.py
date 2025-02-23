"""
Analysis pipeline for processing data through multiple agents with enhanced caching
"""
from typing import Dict, Any, List, Optional
import logging
from ..agents.base_agent import BaseAgent
import asyncio
import pandas as pd
from datetime import datetime
import json
from functools import lru_cache

logger = logging.getLogger(__name__)

class AnalysisCache:
    """Cache for analysis results"""
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self.cache.get(key)
        
    def set(self, key: str, value: Dict[str, Any]) -> None:
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = value

class EnhancedAnalysisPipeline:
    """Enhanced pipeline for coordinating multiple analysis agents with caching"""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self._progress = 0
        self._thoughts = []
        self._results = {}
        self._active_agent = None
        self.MAX_TOTAL_API_CALLS = 5
        self.cache = AnalysisCache()
        self._validate_agents()
        logger.info("Analysis pipeline initialized with agents: %s", list(agents.keys()))

    def _validate_agents(self) -> None:
        """Validate required agents are present"""
        required_agents = {"watson", "gemini", "function"}
        missing = required_agents - set(self.agents.keys())
        if missing:
            raise ValueError(f"Missing required agents: {missing}")

    def _add_thought(self, thought: str) -> None:
        """Add thought with timestamp"""
        self._thoughts.append({
            "thought": thought,
            "timestamp": datetime.now().isoformat(),
            "agent": self._active_agent or "pipeline"
        })

    async def execute(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Execute analysis pipeline with API call limiting and caching"""
        try:
            # Generate cache key from data characteristics
            cache_key = self._generate_cache_key(data)
            cached_result = self.cache.get(cache_key)
            
            if cached_result:
                logger.info("Using cached analysis results")
                self._add_thought("Retrieved cached analysis results")
                return cached_result
            
            logger.info(f"Starting analysis pipeline for dataset shape: {data.shape}")
            self._add_thought(f"Starting analysis of dataset with {len(data)} records")
            
            # Initial data preprocessing
            processed_data = self._preprocess_data(data)
            self._progress = 30
            self._add_thought("Data preprocessing complete")
            logger.info("Data preprocessing complete")
            
            # Prepare batched analysis payload
            analysis_input = self._prepare_analysis_input(processed_data)
            
            # Execute agents in sequence with strict API limits
            api_call_count = 0
            for agent_name, agent in self.agents.items():
                if api_call_count >= self.MAX_TOTAL_API_CALLS:
                    logger.warning(f"Maximum total API calls ({self.MAX_TOTAL_API_CALLS}) reached")
                    break
                    
                try:
                    self._active_agent = agent_name
                    agent_progress_start = 30 + (70 * (list(self.agents.keys()).index(agent_name) / len(self.agents)))
                    
                    self._add_thought(f"Starting {agent_name} analysis")
                    agent_result = await agent.analyze(analysis_input)
                    
                    # Track API calls
                    api_call_count += getattr(agent, '_api_calls', 1)
                    
                    # Store results
                    if agent_result and not isinstance(agent_result.get('error'), str):
                        self._results[agent_name] = agent_result
                    
                    # Update progress
                    self._progress = min(95, int(agent_progress_start + (70/len(self.agents))))
                    
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    self._add_thought(f"Error in {agent_name} analysis: {str(e)}")
                    continue
                    
            # Final processing
            self._progress = 100
            aggregated_results = self._aggregate_results()
            
            # Cache the results
            result = {
                "status": "completed",
                "results": aggregated_results,
                "thoughts": self._thoughts,
                "progress": self._progress,
                "error": None
            }
            self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "thoughts": self._thoughts,
                "progress": self._progress,
                "results": self._results
            }

    def _generate_cache_key(self, data: pd.DataFrame) -> str:
        """Generate a cache key based on data characteristics"""
        characteristics = {
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": str(data.dtypes),
            "head_hash": hash(str(data.head())),
            "timestamp": datetime.now().strftime("%Y%m%d")
        }
        return hash(json.dumps(characteristics, sort_keys=True))

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess data before analysis"""
        # Basic preprocessing
        data = data.copy()
        
        # Handle missing values
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
        data[numeric_cols] = data[numeric_cols].fillna(0)
        data = data.fillna('')
        
        return data

    def _prepare_analysis_input(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Prepare data structure for analysis agents"""
        try:
            # Calculate basic metrics
            metrics = {
                "row_count": len(data),
                "column_count": len(data.columns),
                "missing_values": data.isnull().sum().to_dict(),
                "numeric_summary": self._get_numeric_summary(data),
                "categorical_summary": self._get_categorical_summary(data),
                "completeness": self._calculate_completeness(data)
            }

            # Extract metadata
            metadata = {
                "shape": data.shape,
                "columns": list(data.columns),
                "dtypes": {str(col): str(dtype) for col, dtype in data.dtypes.items()},
                "timestamp": datetime.now().isoformat()
            }

            # Generate patterns
            patterns = self._extract_patterns(data)

            # Add thought markers for transparency
            self._add_thought("Calculated basic metrics")
            self._add_thought("Extracted metadata")
            self._add_thought("Generated data patterns")

            return {
                "data": data.head(1000).to_dict('records'),  # Sample for initial analysis
                "metadata": metadata,
                "metrics": metrics,
                "patterns": patterns
            }

        except Exception as e:
            logger.error(f"Failed to prepare analysis input: {e}")
            self._add_thought(f"Error preparing analysis input: {str(e)}")
            raise

    def _get_numeric_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of numeric columns"""
        numeric_data = data.select_dtypes(include=['int64', 'float64'])
        if numeric_data.empty:
            return {}
            
        summary = numeric_data.describe()
        return {
            col: {
                "mean": summary[col]["mean"],
                "std": summary[col]["std"],
                "min": summary[col]["min"],
                "max": summary[col]["max"],
                "quartiles": [
                    summary[col]["25%"],
                    summary[col]["50%"],
                    summary[col]["75%"]
                ]
            }
            for col in numeric_data.columns
        }

    def _get_categorical_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get summary of categorical columns"""
        categorical_data = data.select_dtypes(include=['object'])
        if categorical_data.empty:
            return {}
            
        return {
            col: {
                "unique_values": categorical_data[col].nunique(),
                "top_values": categorical_data[col].value_counts().head(5).to_dict()
            }
            for col in categorical_data.columns
        }

    def _calculate_completeness(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate data completeness by column"""
        return {
            col: (1 - (data[col].isna().sum() / len(data))) * 100
            for col in data.columns
        }

    def _extract_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract basic patterns from data"""
        patterns = []
        
        # Detect value patterns
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_cols:
            if data[col].nunique() == 1:
                patterns.append({
                    "type": "constant",
                    "column": col,
                    "value": data[col].iloc[0]
                })
            elif data[col].nunique() == 2:
                patterns.append({
                    "type": "binary",
                    "column": col,
                    "values": data[col].unique().tolist()
                })
        
        return patterns

    def _aggregate_results(self) -> Dict[str, Any]:
        """Aggregate results from all agents"""
        aggregated = {
            "summary": {},
            "insights": [],
            "recommendations": []
        }
        
        for agent_name, results in self._results.items():
            # Extract insights
            if "insights" in results:
                aggregated["insights"].extend(
                    [{"agent": agent_name, **insight} 
                     for insight in results["insights"]]
                )
            
            # Extract recommendations
            if "recommendations" in results:
                aggregated["recommendations"].extend(
                    [{"agent": agent_name, **rec} 
                     for rec in results["recommendations"]]
                )
            
            # Merge metrics
            if "metrics" in results:
                aggregated["summary"][agent_name] = results["metrics"]
        
        return aggregated

    async def analyze_dataset(self, df: pd.DataFrame, session_id: str) -> Dict[str, Any]:
        """
        Analyze dataset using multiple agents in parallel
        
        Args:
            df: DataFrame to analyze
            session_id: Unique session identifier
            
        Returns:
            Combined analysis results from all agents
        """
        try:
            logger.info(f"Starting analysis for session {session_id} with shape {df.shape}")
            start_time = datetime.now()
            
            # Prepare common analysis context
            context = {
                "session_id": session_id,
                "timestamp": start_time.isoformat(),
                "data_shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "metrics": {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "missing_values": df.isnull().sum().to_dict()
                }
            }
            
            # Run initial data quality analysis using function agent
            data_quality = await self.agents["function"].analyze({
                "task": "data_quality",
                "data": df.head(1000).to_dict(),  # Sample for initial analysis
                "context": context
            })
            
            # Run parallel analysis with Watson and Gemini
            watson_task = self.agents["watson"].analyze({
                "data": df.to_dict(),
                "context": {**context, "data_quality": data_quality}
            })
            
            gemini_task = self.agents["gemini"].analyze({
                "data": df.to_dict(),
                "context": {**context, "data_quality": data_quality}
            })
            
            # Wait for both analyses to complete
            watson_results, gemini_results = await asyncio.gather(
                watson_task, gemini_task,
                return_exceptions=True
            )
            
            # Handle any errors from individual agents
            for agent_name, result in [("watson", watson_results), ("gemini", gemini_results)]:
                if isinstance(result, Exception):
                    logger.error(f"{agent_name} analysis failed: {result}")
                    result = {
                        "status": "error",
                        "error": str(result),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Combine and synthesize results
            synthesis = await self.agents["function"].analyze({
                "task": "synthesize_results",
                "watson_results": watson_results,
                "gemini_results": gemini_results,
                "data_quality": data_quality,
                "context": context
            })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "data_quality": data_quality,
                "watson_analysis": watson_results,
                "gemini_analysis": gemini_results,
                "synthesis": synthesis,
                "metrics": {
                    **context["metrics"],
                    "processing_time": processing_time
                }
            }
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
