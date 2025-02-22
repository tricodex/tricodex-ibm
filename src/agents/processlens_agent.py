from typing import Any, Dict, List
import logging
import asyncio
from datetime import datetime
from beeai_framework.agents.bee.agent import BeeAgent
from beeai_framework.agents.types import BeeInput, BeeRunInput, BeeRunOutput
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory

logger = logging.getLogger(__name__)

class ProcessLensAgent(BeeAgent):
    """Custom ReAct agent for process analysis using IBM Granite"""
    def __init__(self, llm, tools: List[Any]):
        super().__init__(bee_input=BeeInput(
            llm=llm,
            tools=tools,
            memory=UnconstrainedMemory()
        ))
        self.current_state = "init"
        self.analysis_results = {}
        self.start_time = None
        self.timeout = 300  # 5 minute timeout
        
    async def process_step(self, prompt: str) -> Dict[str, Any]:
        """Execute a single analysis step with thought logging and timeout"""
        if not self.start_time:
            self.start_time = datetime.now()
            
        try:
            # Check timeout
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > self.timeout:
                raise TimeoutError(f"Analysis timeout after {self.timeout} seconds")

            # Execute step with timeout
            result = await asyncio.wait_for(
                self.run(run_input=BeeRunInput(prompt=prompt)),
                timeout=60  # 1 minute timeout per step
            )
            
            # Validate result has new information
            if not self._validate_progress(result):
                raise ValueError("No progress detected in analysis step")
            
            # Log the thought process
            logger.info(f"Agent thought ({self.current_state}): {result.thought}")
            
            # Update state and results
            self.analysis_results[self.current_state] = result.output
            return result.output
            
        except asyncio.TimeoutError:
            logger.error(f"Step timeout in state {self.current_state}")
            raise
        except Exception as e:
            logger.error(f"Error in process step ({self.current_state}): {e}")
            raise

    def _validate_progress(self, result: BeeRunOutput) -> bool:
        """Validate that the step produced new information"""
        if not result or not result.output:
            return False
            
        # Check if output is different from previous state
        prev_output = self.analysis_results.get(self.current_state)
        if prev_output and prev_output == result.output:
            return False
            
        return True

    def reset(self):
        """Reset agent state"""
        self.current_state = "init"
        self.analysis_results = {}
        self.start_time = None

    async def analyze_business_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business metrics and KPIs from data"""
        try:
            prompt = f"""Analyze the following business data and identify:
            1. Key Performance Indicators (KPIs)
            2. Business metrics
            3. Trends and patterns
            4. Actionable recommendations
            
            Data: {data}
            
            Return a structured JSON with the analysis.
            """
            result = await self.run(run_input=BeeRunInput(prompt=prompt))
            return self._validate_and_structure_bi(result)
            
        except Exception as e:
            logger.error(f"Business metrics analysis failed: {e}")
            raise

    def _validate_and_structure_bi(self, result: BeeRunOutput) -> Dict[str, Any]:
        """Validate and structure business intelligence output"""
        if not result or not result.output:
            raise ValueError("Empty analysis result")
            
        try:
            # Structure the output into standard BI format
            structured = {
                "kpis": result.output.get("kpis", []),
                "metrics": result.output.get("metrics", []),
                "trends": result.output.get("trends", []),
                "recommendations": result.output.get("recommendations", [])
            }
            return structured
        except Exception as e:
            logger.error(f"Failed to structure BI output: {e}")
            raise
