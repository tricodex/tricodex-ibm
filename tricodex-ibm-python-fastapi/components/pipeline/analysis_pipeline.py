"""
Core pipeline with caching and parallel processing optimizations
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from utils.helpers import async_retry, ProcessLensError  # Changed from relative to absolute import
from .analysis import Analysis
from ..agents.processlens_agent import ProcessLensAgent
from ..agents.gemini_agent import GeminiAgent
from ..data_processing.ticket_processor import TicketProcessor

logger = logging.getLogger(__name__)

class AnalysisCache:
    """Cache for analysis results"""
    def __init__(self, ttl_minutes: int = 30):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["timestamp"] < self.ttl:
                return entry["data"]
            del self.cache[key]
        return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Cache analysis result"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry"""
        if key in self.cache:
            del self.cache[key]

class EnhancedAnalysisPipeline:
    """Enhanced analysis pipeline with caching and parallel processing"""
    
    def __init__(self, 
                watson_agent: Optional[ProcessLensAgent] = None, 
                gemini_agent: Optional[GeminiAgent] = None,
                cache_ttl: int = 30):
        self.watson_agent = watson_agent
        self.gemini_agent = gemini_agent
        self.processor = TicketProcessor()
        self.cache = AnalysisCache(ttl_minutes=cache_ttl)
        self.progress = 0

    @async_retry(retries=3, delay=1.0)
    async def analyze_dataset(self, 
                            df: pd.DataFrame,
                            cache_key: Optional[str] = None) -> Dict[str, Any]:
        """Run enhanced analysis pipeline"""
        try:
            logger.info(f"Starting analysis pipeline for dataset shape: {df.shape}")
            
            # Validate agents are initialized
            if not self.watson_agent or not self.gemini_agent:
                raise ProcessLensError("Analysis agents not properly initialized")
            
            # Check cache first
            if cache_key:
                cached = self.cache.get(cache_key)
                if cached:
                    logger.info(f"Using cached results for {cache_key}")
                    return cached
            
            # Initial data validation
            if df.empty:
                raise ProcessLensError("Empty dataset provided for analysis")
            
            # Process data with progress tracking
            processed_data = await self._process_with_progress(df)
            self._update_progress(30)
            logger.info("Data preprocessing complete")
            
            # Run parallel analysis with enhanced error handling
            try:
                results = await self._run_parallel_analysis(processed_data)
                self._update_progress(60)
                logger.info("Parallel analysis complete")
            except Exception as e:
                logger.error(f"Parallel analysis failed: {e}", exc_info=True)
                raise ProcessLensError(f"Analysis execution failed: {str(e)}")
            
            # Synthesize and cache results
            try:
                synthesized = await self._synthesize_insights(
                    processed_data=processed_data,
                    **results
                )
                logger.info("Insights synthesis complete")
            except Exception as e:
                logger.error(f"Synthesis failed: {e}", exc_info=True)
                raise ProcessLensError(f"Failed to synthesize insights: {str(e)}")
            
            final_results = {
                "status": "success",
                "processed_data": processed_data,
                "watson_analysis": results["watson_results"],
                "gemini_analysis": results["gemini_results"],
                "synthesized_insights": synthesized,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache results if key provided
            if cache_key:
                self.cache.set(cache_key, final_results)
                logger.info(f"Results cached for key: {cache_key}")
            
            self._update_progress(100)
            return final_results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            if cache_key:
                self.cache.invalidate(cache_key)
            raise ProcessLensError(f"Analysis pipeline failed: {str(e)}")

    async def _process_with_progress(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process data with progress tracking"""
        try:
            return self.processor.process_dataset(df)
        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            raise ProcessLensError(f"Data processing failed: {str(e)}")

    async def _run_parallel_analysis(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis tasks in parallel with error handling"""
        watson_task = self.watson_agent.analyze(processed_data)
        gemini_task = self.gemini_agent.analyze(processed_data)
        
        results = await asyncio.gather(
            watson_task, 
            gemini_task,
            return_exceptions=True
        )
        
        # Handle potential errors from either agent
        watson_results = (
            results[0] if not isinstance(results[0], Exception)
            else {"status": "error", "error": str(results[0])}
        )
        
        gemini_results = (
            results[1] if not isinstance(results[1], Exception)
            else {"status": "error", "error": str(results[1])}
        )
        
        return {
            "watson_results": watson_results,
            "gemini_results": gemini_results
        }

    def _update_progress(self, progress: int) -> None:
        """Update analysis progress"""
        self.progress = progress
        logger.info(f"Analysis progress: {progress}%")

    async def _synthesize_insights(
        self,
        processed_data: Dict[str, Any],
        watson_results: Dict[str, Any],
        gemini_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize insights from both models"""
        try:
            # Extract key metrics and insights
            insights = {
                "key_findings": self._merge_unique_insights(
                    watson_results.get("insights", []),
                    gemini_results.get("insights", [])
                ),
                "recommendations": self._merge_unique_insights(
                    watson_results.get("recommendations", []),
                    gemini_results.get("recommendations", [])
                ),
                "metrics": {
                    **watson_results.get("metrics", {}),
                    **gemini_results.get("metrics", {}),
                    "data_quality": processed_data.get("data_quality", {})
                }
            }
            
            # Add language-specific insights if available
            if "language_insights" in gemini_results:
                insights["language_analysis"] = gemini_results["language_insights"]
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to synthesize insights: {e}")
            return {
                "error": "Failed to synthesize insights",
                "partial_insights": {
                    "watson": watson_results.get("insights", []),
                    "gemini": gemini_results.get("insights", [])
                }
            }

    @staticmethod
    def _merge_unique_insights(list1: List[str], list2: List[str]) -> List[str]:
        """Merge two lists of insights, removing duplicates while preserving order"""
        seen = set()
        merged = []
        
        for item in list1 + list2:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                merged.append(item)
        
        return merged
