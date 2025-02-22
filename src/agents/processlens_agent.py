from typing import Any, Dict, List
import logging
from beeai_framework.agents.bee.agent import BeeAgent
from beeai_framework.agents.types import BeeInput, BeeRunInput, BeeRunOutput
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory

logger = logging.getLogger(__name__)

class ProcessLensAgent(BeeAgent):
    """
    Custom ReAct agent for process analysis using IBM Granite
    """
    def __init__(self, llm, tools: List[Any]):
        super().__init__(bee_input=BeeInput(
            llm=llm,
            tools=tools,
            memory=UnconstrainedMemory()
        ))
        self.current_state = "init"
        self.analysis_results = {}
        
    async def process_step(self, prompt: str) -> Dict[str, Any]:
        """Execute a single analysis step with thought logging"""
        try:
            result = await self.run(
                run_input=BeeRunInput(prompt=prompt)
            )
            
            # Log the thought process
            logger.info(f"Agent thought ({self.current_state}): {result.thought}")
            
            # Update state based on result
            self.analysis_results[self.current_state] = result.output
            return result.output
            
        except Exception as e:
            logger.error(f"Error in process step: {e}")
            raise
