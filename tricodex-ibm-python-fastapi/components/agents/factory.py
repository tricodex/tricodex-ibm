"""
Agent factory for managing LLM instances
"""
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime
import logging
import asyncio
import os
from beeai_framework import BaseAgent
from langchain_ibm import WatsonxLLM
from google import genai  # Updated Gemini import
from .watson_agent import WatsonAgent
from .gemini_agent import GeminiAgent
from .function_calling_agent import FunctionCallingAgent
from config import Config

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating and managing LLM agent instances"""
    
    _instances: Dict[str, Any] = {}
    _initialization_time: Dict[str, datetime] = {}
    _MAX_RETRY_ATTEMPTS = 3
    _RETRY_DELAY = 1.0  # seconds
    
    @classmethod
    async def initialize_agents(cls) -> Tuple[bool, Optional[str]]:
        """Initialize all required agents with proper error handling"""
        errors = []
        try:
            # Watson Configuration
            watson_config = {
                "model_id": os.getenv("WATSON_MODEL_ID", "ibm/granite-13b-instruct-v2"),  # Updated model ID
                "api_key": os.getenv("IBM_API_KEY"),
                "project_id": os.getenv("PROJECT_ID"),
                "url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
                "params": {
                    "decoding_method": "greedy",
                    "max_new_tokens": 1024,
                    "min_new_tokens": 50,
                    "temperature": 0.7,
                    "top_p": 0.7,
                    "top_k": 50,
                    "repetition_penalty": 1.2,
                    "stop_sequences": []
                }
            }

            # Gemini Configuration
            gemini_config = {
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "model": "gemini-2.0-flash",
                "http_options": {"api_version": "v1alpha"}
            }

            # Validate configurations
            if not cls._validate_config("watson", watson_config):
                errors.append("Invalid Watson configuration")
            if not cls._validate_config("gemini", gemini_config):
                errors.append("Invalid Gemini configuration")

            if errors:
                return False, "\n".join(errors)

            # Create instances
            cls._instances["watson"] = await cls._create_agent("watson", watson_config)
            cls._instances["gemini"] = await cls._create_agent("gemini", gemini_config)

            # Test connections
            for agent_type, agent in cls._instances.items():
                if not await cls._test_agent(agent, agent_type):
                    errors.append(f"Connection test failed for {agent_type}")

            if errors:
                return False, "\n".join(errors)

            # Record initialization time
            now = datetime.now()
            for agent_type in cls._instances:
                cls._initialization_time[agent_type] = now

            return True, None

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            return False, str(e)

    @classmethod
    def _validate_config(cls, agent_type: str, config: Dict[str, Any]) -> bool:
        """Validate agent configuration"""
        required_fields = {
            "watson": ["model_id", "api_key", "project_id", "url"],
            "gemini": ["api_key", "model"],
            "function": ["model_id", "api_key", "project_id", "url"]
        }

        if agent_type not in required_fields:
            logger.error(f"Unknown agent type: {agent_type}")
            return False

        missing_fields = [field for field in required_fields[agent_type] 
                         if not config.get(field)]
        
        if missing_fields:
            logger.error(f"Missing required fields for {agent_type}: {missing_fields}")
            return False
            
        return True

    @classmethod
    async def _test_agent(cls, agent: Union[WatsonAgent, GeminiAgent, FunctionCallingAgent], 
                         agent_type: str) -> bool:
        """Test agent connection with timeout"""
        if not agent:
            logger.error(f"No agent instance available for {agent_type}")
            return False

        try:
            # More detailed test input
            test_input = {
                "input": "Test connection",
                "metadata": {"test": True},
                "metrics": {"dummy": 1},
                "patterns": [],
                "data_quality": {"complete": True}
            }
            
            logger.info(f"Starting connection test for {agent_type}")
            await asyncio.wait_for(
                agent.analyze(test_input), 
                timeout=60.0  # Increased timeout for initial connection
            )
            logger.info(f"Connection test successful for {agent_type}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection test timeout for {agent_type} after 60 seconds")
            return False
        except Exception as e:
            logger.error(f"Connection test failed for {agent_type}: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def _create_agent(cls, agent_type: str, timeout: int = 300) -> BaseAgent:
        """Create an agent instance with proper initialization"""
        try:
            config = Config.get_model_config(agent_type)
            
            if agent_type == "watson":
                logger.info("Creating watson agent")
                return WatsonAgent(
                    model_id=config["model_id"],
                    api_key=config["api_key"],
                    project_id=config["project_id"],
                    url=config["url"],
                    timeout=timeout
                )
                
            elif agent_type == "gemini":
                logger.info("Creating gemini agent")
                return GeminiAgent(config=config, timeout=timeout)
                
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
                
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent: {e}")
            raise

    @classmethod
    def get_agent(cls, agent_type: str) -> Optional[Any]:
        """Get initialized agent instance"""
        return cls._instances.get(agent_type)

    @classmethod
    def reset_agents(cls) -> None:
        """Reset all agent instances"""
        for agent_type, agent in cls._instances.items():
            try:
                if hasattr(agent, 'cleanup'):
                    asyncio.create_task(agent.cleanup())
                logger.info(f"Reset {agent_type} agent")
            except Exception as e:
                logger.error(f"Error resetting {agent_type} agent: {e}")
        
        cls._instances.clear()
        cls._initialization_time.clear()
        logger.info("All agent instances reset")

    @classmethod
    def get_agent_status(cls) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        now = datetime.now()
        
        for agent_type, init_time in cls._initialization_time.items():
            agent = cls._instances.get(agent_type)
            status[agent_type] = {
                "initialized": agent is not None,
                "uptime": str(now - init_time) if init_time else None,
                "last_error": getattr(agent, "_last_error", None) if agent else None,
                "error_count": getattr(agent, "_error_count", 0) if agent else 0
            }
            
        return status