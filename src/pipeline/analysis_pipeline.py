import asyncio
import logging
from typing import Any, Dict, List
import pandas as pd
from ..agents.processlens_agent import ProcessLensAgent
from ..agents.function_calling_agent import FunctionCallingAgent
from ..agents.gemini_agent import GeminiAgent

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """Coordinates the process analysis pipeline using the ProcessLensAgent"""
    def __init__(self, watson_agent: ProcessLensAgent, gemini_agent: GeminiAgent, model_params: Dict[str, Any]):
        self.watson_agent = watson_agent
        self.gemini_agent = gemini_agent
        self.function_agent = FunctionCallingAgent(model_params)
        self.state = "init"
        self.results = {}
        self.progress = 0

    async def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run the complete analysis pipeline with ticket processing"""
        try:
            from ..data_processing.ticket_processor import TicketProcessor
            
            # Process ticket data
            processor = TicketProcessor()
            processed_data = processor.process_dataset(df)
            self._update_progress(30)
            
            # Run parallel analysis with both agents
            watson_task = self.watson_agent.analyze_tickets(processed_data)
            gemini_task = self.gemini_agent.analyze_tickets(processed_data)
            
            watson_insights, gemini_insights = await asyncio.gather(watson_task, gemini_task)
            self._update_progress(60)
            
            # Standardize both outputs
            watson_results = self._standardize_watson_output(watson_insights)
            gemini_results = self._standardize_gemini_output(gemini_insights)
            
            # Enhanced analysis with function calling
            enhanced_analysis = await self.function_agent.function_call(
                "Compare and synthesize insights from both models",
                {
                    "watson_insights": watson_results,
                    "gemini_insights": gemini_results,
                    "processed_data": processed_data
                }
            )
            
            self._update_progress(90)
            
            # Structure final results
            results = {
                "processed_data": processed_data,
                "watson_results": watson_results,
                "gemini_results": gemini_results,
                "enhanced_analysis": enhanced_analysis,
                "status": "success"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}")
            self._update_progress(-1)
            return {
                "status": "error",
                "error": str(e),
                "partial_results": self.results
            }

    def _update_progress(self, progress: int):
        """Update analysis progress"""
        self.progress = progress
        logger.info(f"Analysis progress: {progress}%")

    async def _analyze_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced structure analysis with function calling"""
        # Get initial structure analysis
        structure = await super()._analyze_structure(df)
        
        # Enhance with function calling analysis
        logger.info("Function Agent: Enhancing structure analysis with KPI detection")
        kpi_analysis = await self.function_agent.function_call(
            "Analyze key business metrics and KPIs in the data structure",
            {"structure": structure}
        )
        
        return {**structure, "kpi_analysis": kpi_analysis}

    async def _mine_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced pattern mining with function calling"""
        # Get initial patterns
        patterns = await super()._mine_patterns(df)
        
        # Enhance with efficiency analysis
        logger.info("Function Agent: Analyzing process efficiency patterns")
        efficiency_analysis = await self.function_agent.function_call(
            "Analyze process efficiency and identify optimization opportunities",
            {"patterns": patterns}
        )
        
        return {**patterns, "efficiency_analysis": efficiency_analysis}

    async def _generate_optimizations(self) -> Dict[str, Any]:
        """Generate business-focused optimization recommendations"""
        prompt = f"""Based on:
        Structure: {self.results['structure']}
        Patterns: {self.results['patterns']}
        
        Generate business optimization recommendations:
        1. Revenue optimization opportunities
        2. Cost reduction strategies
        3. Process efficiency improvements
        4. Customer experience enhancements
        5. Resource allocation suggestions
        
        Include expected impact and implementation steps in JSON.
        """
        return await self.agent.process_step(prompt)

    def _standardize_watson_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize WatsonX output format"""
        return {
            "insights": output.get("insights", []),
            "patterns": output.get("patterns", []),
            "recommendations": output.get("recommendations", []),
            "metrics": output.get("metrics", {}),
            "quality_impact": output.get("data_quality_impact", {})
        }

    def _standardize_gemini_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize Gemini output format"""
        return {
            "insights": output.get("insights", []),
            "bottlenecks": output.get("bottlenecks", []),
            "recommendations": output.get("recommendations", []),
            "quality_impact": output.get("data_quality_impact", {}),
            "language_analysis": output.get("language_considerations", {})
        }
