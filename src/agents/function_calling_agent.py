import re
from typing import Dict, Any, List
import logging
import json
from transformers import AutoTokenizer
from langchain_ibm import WatsonxLLM

logger = logging.getLogger(__name__)

class FunctionCallingAgent:
    """Agent that handles IBM watsonx function calling capabilities"""
    
    def __init__(self, model_params: Dict[str, Any]):
        self.tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-3.1-8b-instruct")
        self.model = WatsonxLLM(**model_params)
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define available business analysis tools"""
        return [
            {
                "name": "analyze_kpis",
                "description": "Analyze key performance indicators from business data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metrics": {"type": "array", "items": {"type": "object"}},
                        "time_period": {"type": "string"},
                        "target_goals": {"type": "object"}
                    },
                    "required": ["metrics"]
                }
            },
            {
                "name": "process_efficiency",
                "description": "Analyze process efficiency and bottlenecks",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "process_data": {"type": "object"},
                        "time_metrics": {"type": "object"}
                    },
                    "required": ["process_data"]
                }
            }
        ]

    async def function_call(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function calling with thought process logging"""
        try:
            # Prepare conversation for function calling
            conversation = [
                {"role": "system", "content": "You are a business analysis assistant."},
                {"role": "user", "content": query}
            ]

            # Generate instruction with tools
            instruction = self.tokenizer.apply_chat_template(
                conversation=conversation,
                tools=self.tools,
                tokenize=False,
                add_generation_prompt=True
            )

            # Log thought process
            logger.info(f"Function Calling Agent thought: Analyzing query '{query}'")

            # Execute function calling
            response = self.model.invoke(instruction)
            
            # Parse and validate response
            result = self._parse_response(response)
            
            logger.info(f"Function Calling Agent thought: Selected function '{result.get('name', 'unknown')}'")
            
            return result

        except Exception as e:
            logger.error(f"Function calling failed: {e}")
            raise

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate function calling response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found in response")
                
            result = json.loads(json_match.group())
            return result

        except Exception as e:
            logger.error(f"Failed to parse function response: {e}")
            raise
