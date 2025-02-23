"""
Function calling capabilities for LLM agents with enhanced process metrics
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import time
from .watson_agent import WatsonAgent
from .gemini_agent import GeminiAgent
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class FunctionCallingAgent(BaseAgent):
    """Agent with function calling capabilities combining Watson and Gemini"""
    
    def __init__(self, watson_agent: WatsonAgent, gemini_agent: GeminiAgent, timeout: int = 300):
        super().__init__(timeout)
        self.watson = watson_agent
        self.gemini = gemini_agent
        self._api_calls = 0
        self._last_call_time = 0
        
    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute combined analysis using both Watson and Gemini"""
        try:
            logger.info("Starting combined analysis")
            start_time = time.time()
            
            # Run analysis in parallel
            watson_future = self.watson._run_analysis(data)
            gemini_future = self.gemini._run_analysis(data)
            
            # Gather results
            watson_result, gemini_result = await asyncio.gather(
                watson_future, 
                gemini_future,
                return_exceptions=True
            )
            
            # Handle potential errors
            if isinstance(watson_result, Exception):
                logger.error(f"Watson analysis failed: {watson_result}")
                watson_result = {}
            if isinstance(gemini_result, Exception):
                logger.error(f"Gemini analysis failed: {gemini_result}")
                gemini_result = {}
                
            # Merge and enhance results
            combined_results = await self._merge_results(watson_result, gemini_result)
            
            # Add meta-analysis
            if combined_results:
                meta_insights = await self._generate_meta_insights(combined_results)
                combined_results["meta_analysis"] = meta_insights
            
            execution_time = time.time() - start_time
            logger.info(f"Combined analysis completed in {execution_time:.2f}s")
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Combined analysis failed: {e}")
            raise
            
    async def _merge_results(self, watson_results: Dict[str, Any], gemini_results: Dict[str, Any]) -> Dict[str, Any]:
        """Merge and reconcile results from both models"""
        try:
            merged = {
                "insights": [],
                "patterns": [],
                "metrics": {},
                "recommendations": [],
                "data_quality": {},
                "synthesis": {}
            }
            
            # Merge insights with source attribution
            merged["insights"].extend([{"source": "watson", "insight": i} for i in watson_results.get("insights", [])])
            merged["insights"].extend([{"source": "gemini", "insight": i} for i in gemini_results.get("insights", [])])
            
            # Merge patterns with deduplication
            all_patterns = []
            seen_patterns = set()
            
            for pattern in watson_results.get("patterns", []) + gemini_results.get("patterns", []):
                pattern_key = f"{pattern.get('name', '')}_{pattern.get('type', '')}"
                if pattern_key not in seen_patterns:
                    seen_patterns.add(pattern_key)
                    all_patterns.append(pattern)
            
            merged["patterns"] = all_patterns
            
            # Merge metrics with averaging for duplicates
            all_metrics = {}
            for source, results in [("watson", watson_results), ("gemini", gemini_results)]:
                for key, metric in results.get("metrics", {}).items():
                    if key not in all_metrics:
                        all_metrics[key] = {"values": [], "units": set()}
                    all_metrics[key]["values"].append(metric.get("value", 0))
                    all_metrics[key]["units"].add(metric.get("unit", ""))
                    
            # Average metrics and resolve unit conflicts
            for key, data in all_metrics.items():
                avg_value = sum(data["values"]) / len(data["values"])
                units = list(data["units"])
                merged["metrics"][key] = {
                    "value": avg_value,
                    "unit": units[0] if len(units) == 1 else "mixed",
                    "confidence": 1.0 if len(units) == 1 else 0.5
                }
            
            # Combine recommendations with source tracking
            for source, results in [("watson", watson_results), ("gemini", gemini_results)]:
                for rec in results.get("recommendations", []):
                    rec["source"] = source
                    merged["recommendations"].append(rec)
            
            # Merge data quality assessments
            merged["data_quality"] = {
                "watson": watson_results.get("data_quality", {}),
                "gemini": gemini_results.get("data_quality", {}),
            }
            
            # Add synthesis section
            merged["synthesis"] = {
                "agreement_level": self._calculate_agreement(watson_results, gemini_results),
                "complementary_insights": self._find_complementary_insights(
                    watson_results.get("insights", []),
                    gemini_results.get("insights", [])
                )
            }
            
            return merged
            
        except Exception as e:
            logger.error(f"Failed to merge results: {e}")
            raise
            
    def _calculate_agreement(self, watson_results: Dict[str, Any], gemini_results: Dict[str, Any]) -> float:
        """Calculate agreement level between Watson and Gemini results"""
        try:
            # Compare patterns
            watson_patterns = {p.get("name") for p in watson_results.get("patterns", [])}
            gemini_patterns = {p.get("name") for p in gemini_results.get("patterns", [])}
            
            if watson_patterns or gemini_patterns:
                pattern_agreement = len(watson_patterns & gemini_patterns) / len(watson_patterns | gemini_patterns)
            else:
                pattern_agreement = 0
                
            # Compare metrics
            watson_metrics = set(watson_results.get("metrics", {}).keys())
            gemini_metrics = set(gemini_results.get("metrics", {}).keys())
            
            if watson_metrics or gemini_metrics:
                metric_agreement = len(watson_metrics & gemini_metrics) / len(watson_metrics | gemini_metrics)
            else:
                metric_agreement = 0
                
            # Calculate weighted agreement
            return (pattern_agreement * 0.6) + (metric_agreement * 0.4)
            
        except Exception as e:
            logger.warning(f"Failed to calculate agreement: {e}")
            return 0.0
            
    def _find_complementary_insights(self, watson_insights: List[str], gemini_insights: List[str]) -> List[Dict[str, Any]]:
        """Identify complementary insights between models"""
        complementary = []
        
        # Find unique themes in each set
        watson_themes = set(self._extract_themes(watson_insights))
        gemini_themes = set(self._extract_themes(gemini_insights))
        
        # Identify unique contributions
        watson_unique = watson_themes - gemini_themes
        gemini_unique = gemini_themes - watson_themes
        
        if watson_unique:
            complementary.append({
                "source": "watson",
                "unique_themes": list(watson_unique)
            })
            
        if gemini_unique:
            complementary.append({
                "source": "gemini",
                "unique_themes": list(gemini_unique)
            })
            
        return complementary
        
    def _extract_themes(self, insights: List[str]) -> List[str]:
        """Extract key themes from insights"""
        themes = set()
        
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = ["performance", "efficiency", "bottleneck", "improvement",
                   "quality", "cost", "time", "resource", "risk"]
                   
        for insight in insights:
            for keyword in keywords:
                if keyword in insight.lower():
                    themes.add(keyword)
                    
        return list(themes)
        
    async def _generate_meta_insights(self, combined_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meta-analysis of the combined results"""
        try:
            meta_insights = {
                "model_agreement": combined_results["synthesis"]["agreement_level"],
                "confidence_levels": {
                    "high": [],
                    "medium": [],
                    "low": []
                },
                "cross_validation": []
            }
            
            # Analyze confidence levels
            for pattern in combined_results["patterns"]:
                confidence = self._assess_pattern_confidence(pattern)
                if confidence >= 0.8:
                    meta_insights["confidence_levels"]["high"].append(pattern["name"])
                elif confidence >= 0.5:
                    meta_insights["confidence_levels"]["medium"].append(pattern["name"])
                else:
                    meta_insights["confidence_levels"]["low"].append(pattern["name"])
            
            # Cross-validate findings
            meta_insights["cross_validation"] = await self._cross_validate_findings(combined_results)
            
            return meta_insights
            
        except Exception as e:
            logger.error(f"Failed to generate meta-insights: {e}")
            return {}
            
    def _assess_pattern_confidence(self, pattern: Dict[str, Any]) -> float:
        """Assess confidence in a detected pattern"""
        confidence = 0.5  # Base confidence
        
        # Adjust based on frequency
        if "frequency" in pattern:
            confidence += min(0.3, pattern["frequency"] / 100)
            
        # Adjust based on performance metrics
        if "performance_metrics" in pattern:
            confidence += 0.2
            
        return min(1.0, confidence)
        
    async def _cross_validate_findings(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cross-validate findings between models"""
        validations = []
        
        # Group insights by theme
        insights_by_theme = {}
        for insight in results["insights"]:
            themes = self._extract_themes([insight["insight"]])
            for theme in themes:
                if theme not in insights_by_theme:
                    insights_by_theme[theme] = {"watson": [], "gemini": []}
                insights_by_theme[theme][insight["source"]].append(insight["insight"])
        
        # Analyze agreement for each theme
        for theme, sources in insights_by_theme.items():
            if sources["watson"] and sources["gemini"]:
                validations.append({
                    "theme": theme,
                    "agreement": "high" if len(sources["watson"]) + len(sources["gemini"]) > 2 else "medium",
                    "watson_count": len(sources["watson"]),
                    "gemini_count": len(sources["gemini"])
                })
        
        return validations