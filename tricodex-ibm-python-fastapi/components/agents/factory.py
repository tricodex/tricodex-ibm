"""
Agent factory for creating and managing LLM agents
"""
from typing import Dict, Any, Optional, Type
from .base_agent import BaseAgent
from .processlens_agent import ProcessLensAgent
from .gemini_agent import GeminiAgent
from .function_calling_agent import FunctionCallingAgent
from config import Config
from langchain_ibm import WatsonxLLM
from google import genai
import logging

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating and managing LLM agents"""
    
    _instances: Dict[str, BaseAgent] = {}
    
    @classmethod
    def create_agent(cls, 
                   agent_type: str,
                   config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """
        Create or retrieve an agent instance
        
        Args:
            agent_type: Type of agent to create ('watson', 'gemini', or 'function')
            config: Optional configuration override
        """
        if agent_type in cls._instances:
            return cls._instances[agent_type]
            
        agent = cls._create_new_agent(agent_type, config)
        cls._instances[agent_type] = agent
        return agent
    
    @classmethod
    def _create_new_agent(cls, 
                         agent_type: str, 
                         config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """Create a new agent instance"""
        try:
            if agent_type == "watson":
                model_config = config or Config.WATSON_CONFIG
                model = WatsonxLLM(**model_config)
                return ProcessLensAgent(
                    llm=model,
                    tools=[],
                    timeout=Config.DEFAULT_TIMEOUT
                )
                
            elif agent_type == "gemini":
                api_key = (config or Config.GEMINI_CONFIG)["api_key"]
                return GeminiAgent(
                    api_key=api_key,
                    timeout=Config.DEFAULT_TIMEOUT
                )
                
            elif agent_type == "function":
                model_config = config or Config.WATSON_CONFIG
                return FunctionCallingAgent(
                    model_params=model_config,
                    timeout=Config.DEFAULT_TIMEOUT
                )
                
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
                
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type}: {e}")
            raise
    
    @classmethod
    def reset_agents(cls) -> None:
        """Reset all agent instances"""
        cls._instances.clear()
        
    @classmethod
    def get_agent(cls, agent_type: str) -> Optional[BaseAgent]:
        """Get existing agent instance if available"""
        return cls._instances.get(agent_type)