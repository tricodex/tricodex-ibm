import logging
from typing import Any, Dict, List
import pandas as pd
from ..agents.processlens_agent import ProcessLensAgent
from ..agents.function_calling_agent import FunctionCallingAgent

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """Coordinates the process analysis pipeline using the ProcessLensAgent"""
    def __init__(self, agent: ProcessLensAgent, model_params: Dict[str, Any]):
        self.agent = agent
        self.function_agent = FunctionCallingAgent(model_params)
        self.state = "init"
        self.results = {}
        self.progress = 0

    async def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run the complete analysis pipeline with progress tracking"""
        try:
            # Reset agent state
            self.agent.reset()
            self._update_progress(0)
            
            # Structure Analysis
            self.state = "structure_analysis"
            structure = await self._analyze_structure(df)
            self.results["structure"] = structure
            self._update_progress(33)
            
            # Pattern Mining
            self.state = "pattern_mining"
            patterns = await self._mine_patterns(df)
            self.results["patterns"] = patterns
            self._update_progress(66)
            
            # Process Optimization
            self.state = "optimization"
            optimizations = await self._generate_optimizations()
            self.results["optimizations"] = optimizations
            self._update_progress(100)
            
            return self.results
            
        except Exception as e:
            logger.error(f"Pipeline error in state {self.state}: {e}")
            self._update_progress(-1)  # Signal error
            raise

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
