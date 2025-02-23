"""
Function calling capabilities for LLM agents with enhanced process metrics
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import json
import re
from datetime import datetime, timedelta
import pandas as pd
from transformers import AutoTokenizer
from langchain_ibm import WatsonxLLM
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class FunctionCallSchema:
    """Schema definitions for function calling"""
    KPI_ANALYSIS = {
        "name": "analyze_kpis",
        "description": "Analyze key performance indicators",
        "parameters": {
            "type": "object",
            "properties": {
                "metrics": {"type": "array", "items": {"type": "object"}},
                "time_period": {"type": "string"},
                "target_goals": {"type": "object"}
            },
            "required": ["metrics"]
        }
    }
    
    PROCESS_EFFICIENCY = {
        "name": "process_efficiency",
        "description": "Analyze process efficiency",
        "parameters": {
            "type": "object",
            "properties": {
                "process_data": {"type": "object"},
                "time_metrics": {"type": "object"}
            },
            "required": ["process_data"]
        }
    }

class FunctionCallingAgent(BaseAgent):
    """Agent that handles function calling capabilities"""
    
    def __init__(self, model_params: Dict[str, Any], timeout: int = 300):
        super().__init__(timeout)
        self.tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-3.1-8b-instruct")
        self.model = WatsonxLLM(**model_params)
        self.available_functions = [
            FunctionCallSchema.KPI_ANALYSIS,
            FunctionCallSchema.PROCESS_EFFICIENCY
        ]

    async def _run_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function calling analysis"""
        try:
            # Prepare system context
            conversation = [
                {"role": "system", "content": "You are a business process analysis assistant."},
                {"role": "user", "content": self._create_analysis_prompt(data)}
            ]

            # Generate instruction with functions
            instruction = self.tokenizer.apply_chat_template(
                conversation=conversation,
                tools=self.available_functions,
                tokenize=False,
                add_generation_prompt=True
            )

            # Execute function calling
            response = await self.model.agenerate(instruction)
            result = self._parse_function_response(response)
            
            # Execute the called function
            if result.get("name") == "analyze_kpis":
                return await self._analyze_kpis(result.get("arguments", {}), data)
            elif result.get("name") == "process_efficiency":
                return await self._analyze_process_efficiency(result.get("arguments", {}), data)
            else:
                raise ValueError(f"Unknown function: {result.get('name')}")

        except Exception as e:
            logger.error(f"Function calling failed: {e}")
            raise

    def _calculate_throughput(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate process throughput metrics"""
        try:
            total_tickets = process_data.get("total_records", 0)
            time_metrics = process_data.get("time_metrics", {})
            resolution_times = time_metrics.get("resolution_times", [])
            
            if not resolution_times:
                return {
                    "daily_throughput": 0,
                    "weekly_throughput": 0,
                    "average_processing_time": 0
                }
            
            # Calculate time-based metrics
            time_range = max(resolution_times) - min(resolution_times)
            days_span = time_range.days or 1  # Avoid division by zero
            
            throughput_metrics = {
                "daily_throughput": total_tickets / days_span,
                "weekly_throughput": (total_tickets / days_span) * 7,
                "average_processing_time": sum(
                    (t.total_seconds() for t in resolution_times if t),
                    start=0
                ) / len(resolution_times) if resolution_times else 0
            }
            
            return {
                **throughput_metrics,
                "confidence": self._calculate_confidence(throughput_metrics)
            }
            
        except Exception as e:
            logger.error(f"Throughput calculation failed: {e}")
            return {"error": str(e)}

    def _identify_bottlenecks(self, process_data: Dict[str, Any], 
                            time_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify process bottlenecks"""
        try:
            bottlenecks = []
            
            # Analyze response times
            response_times = time_metrics.get("first_response_times", [])
            if response_times:
                avg_response = sum(t.total_seconds() for t in response_times) / len(response_times)
                if avg_response > 3600:  # More than 1 hour
                    bottlenecks.append({
                        "type": "response_time",
                        "severity": "high" if avg_response > 7200 else "medium",
                        "metric": avg_response,
                        "impact": "Long first response times affecting customer satisfaction"
                    })
            
            # Analyze resolution times
            resolution_times = time_metrics.get("resolution_times", [])
            if resolution_times:
                avg_resolution = sum(t.total_seconds() for t in resolution_times) / len(resolution_times)
                if avg_resolution > 86400:  # More than 24 hours
                    bottlenecks.append({
                        "type": "resolution_time",
                        "severity": "high" if avg_resolution > 172800 else "medium",
                        "metric": avg_resolution,
                        "impact": "Extended resolution times indicating process delays"
                    })
            
            # Analyze workload distribution
            agent_loads = process_data.get("agent_workload", {})
            if agent_loads:
                avg_load = sum(agent_loads.values()) / len(agent_loads)
                overloaded_agents = [
                    agent for agent, load in agent_loads.items()
                    if load > avg_load * 1.5
                ]
                if overloaded_agents:
                    bottlenecks.append({
                        "type": "workload_imbalance",
                        "severity": "medium",
                        "affected_agents": overloaded_agents,
                        "impact": "Uneven workload distribution causing delays"
                    })
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Bottleneck identification failed: {e}")
            return [{"error": str(e)}]

    def _calculate_resource_utilization(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resource utilization metrics"""
        try:
            # Extract resource data
            agent_metrics = process_data.get("agent_metrics", {})
            time_metrics = process_data.get("time_metrics", {})
            
            # Calculate utilization rates
            total_time = sum(time_metrics.get("handling_times", [0]))
            available_time = sum(time_metrics.get("available_times", [0]))
            
            utilization = {
                "overall_utilization": (total_time / available_time) if available_time else 0,
                "agent_utilization": {},
                "peak_hours": self._identify_peak_hours(process_data),
                "resource_efficiency": self._calculate_efficiency_metrics(agent_metrics)
            }
            
            # Add agent-specific metrics
            for agent, metrics in agent_metrics.items():
                agent_total = metrics.get("total_time", 0)
                agent_available = metrics.get("available_time", 0)
                utilization["agent_utilization"][agent] = {
                    "rate": (agent_total / agent_available) if agent_available else 0,
                    "ticket_count": metrics.get("ticket_count", 0),
                    "average_handling_time": metrics.get("avg_handling_time", 0)
                }
            
            return utilization
            
        except Exception as e:
            logger.error(f"Resource utilization calculation failed: {e}")
            return {"error": str(e)}

    def _identify_peak_hours(self, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify peak activity hours"""
        try:
            hourly_counts = process_data.get("hourly_distribution", {})
            if not hourly_counts:
                return {}
            
            avg_count = sum(hourly_counts.values()) / len(hourly_counts)
            peak_hours = {
                hour: count
                for hour, count in hourly_counts.items()
                if count > avg_count * 1.2  # 20% above average
            }
            
            return {
                "peak_hours": peak_hours,
                "average_load": avg_count,
                "peak_load_factor": max(peak_hours.values()) / avg_count if peak_hours else 1
            }
            
        except Exception as e:
            logger.error(f"Peak hours identification failed: {e}")
            return {"error": str(e)}

    def _calculate_efficiency_metrics(self, agent_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate efficiency-related metrics"""
        try:
            all_handling_times = []
            all_resolution_rates = []
            
            for metrics in agent_metrics.values():
                if "handling_times" in metrics:
                    all_handling_times.extend(metrics["handling_times"])
                if "resolution_rate" in metrics:
                    all_resolution_rates.append(metrics["resolution_rate"])
            
            return {
                "average_handling_time": sum(all_handling_times) / len(all_handling_times) if all_handling_times else 0,
                "handling_time_variance": self._calculate_variance(all_handling_times),
                "resolution_rate": sum(all_resolution_rates) / len(all_resolution_rates) if all_resolution_rates else 0
            }
            
        except Exception as e:
            logger.error(f"Efficiency metrics calculation failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def _calculate_variance(values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        squared_diff = sum((x - mean) ** 2 for x in values)
        return squared_diff / len(values)

    @staticmethod
    def _calculate_confidence(metrics: Dict[str, float]) -> float:
        """Calculate confidence score for metrics"""
        if not metrics:
            return 0
        
        # Check for invalid values
        if any(not isinstance(v, (int, float)) or v < 0 for v in metrics.values()):
            return 0
        
        # Basic confidence calculation
        return min(1.0, sum(1 for v in metrics.values() if v > 0) / len(metrics))

    def _analyze_time_period(self, metrics: Dict[str, Any], 
                           time_period: Optional[str]) -> Dict[str, Any]:
        """Analyze metrics over specified time period"""
        try:
            if not time_period:
                return {}
                
            # Extract time-based metrics
            time_metrics = {
                k: v for k, v in metrics.items()
                if isinstance(v, (datetime, pd.Timestamp))
            }
            
            if not time_metrics:
                return {}
            
            # Calculate period statistics
            start_time = min(time_metrics.values())
            end_time = max(time_metrics.values())
            duration = end_time - start_time
            
            return {
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
                "duration_days": duration.days,
                "metrics_count": len(time_metrics),
                "daily_average": len(time_metrics) / (duration.days or 1)
            }
            
        except Exception as e:
            logger.error(f"Time period analysis failed: {e}")
            return {"error": str(e)}

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create structured analysis prompt"""
        # Extract key metrics for the prompt
        metrics = data.get("metrics", {})
        patterns = data.get("patterns", [])
        metadata = data.get("metadata", {})
        
        return f"""Analyze this process data and provide insights:
        
        Process Metrics:
        {json.dumps(metrics, indent=2)}
        
        Patterns:
        {json.dumps(patterns, indent=2)}
        
        Metadata:
        {json.dumps(metadata, indent=2)}
        
        Analyze the following aspects:
        1. Key performance indicators and their trends
        2. Process efficiency and bottlenecks
        3. Resource utilization patterns
        4. Recommendations for improvement
        
        Focus on actionable insights and quantitative analysis.
        Return results using the appropriate function call.
        """

    def _parse_function_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate function calling response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found in response")
                
            result = json.loads(json_match.group())
            
            # Validate function name
            if "name" not in result or result["name"] not in {f["name"] for f in self.available_functions}:
                raise ValueError("Invalid function name in response")
                
            # Ensure arguments are present
            if "arguments" not in result:
                result["arguments"] = {}
                
            return result

        except Exception as e:
            logger.error(f"Failed to parse function response: {e}")
            raise

    def _stringify_keys(self, obj: Any) -> Any:
        """Recursively convert all dictionary keys to strings"""
        if isinstance(obj, dict):
            return {str(key): self._stringify_keys(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._stringify_keys(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._stringify_keys(item) for item in obj)
        return obj

    def _sanitize_numeric_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all numeric values are properly formatted for JSON"""
        def _sanitize(value: Any) -> Any:
            if isinstance(value, (float, int)):
                return float(value) if isinstance(value, float) else value
            elif isinstance(value, dict):
                return {k: _sanitize(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [_sanitize(item) for item in value]
            return value
            
        return _sanitize(data)

    def _validate_timestamps(self, timestamps: List[Any]) -> List[datetime]:
        """Validate and convert timestamp values"""
        valid_timestamps = []
        for ts in timestamps:
            try:
                if isinstance(ts, str):
                    valid_timestamps.append(datetime.fromisoformat(ts))
                elif isinstance(ts, (datetime, pd.Timestamp)):
                    valid_timestamps.append(ts)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp value: {ts}, Error: {e}")
                continue
        return valid_timestamps

    async def _handle_response_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors in function responses"""
        logger.error(f"Function response error: {error}")
        return {
            "status": "error",
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "partial_results": getattr(error, "partial_results", None)
        }