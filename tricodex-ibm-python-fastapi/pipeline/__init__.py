"""
ProcessLens Pipeline: Core agents and functionality for process mining
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass
from langchain_ibm import WatsonxLLM
from langchain.agents import Tool, AgentExecutor, BaseMultiActionAgent
from langchain.tools import BaseTool
import json

@dataclass
class MetricsAgent:
    """Base agent class for process metrics calculation"""
    model: WatsonxLLM
    tools: List[BaseTool]
    
    async def analyze(self, df: pd.DataFrame) -> Dict[str, float]:
        raise NotImplementedError
        
    async def _execute_analysis(self, df: pd.DataFrame, function_spec: Dict, context: Dict, prompt: str = None) -> Dict:
        """Execute analysis using function calling"""
        if not prompt:
            prompt = f"""
            Analyze the process metrics based on the following context:
            {json.dumps(context, indent=2)}
            
            Provide detailed analysis with supporting evidence and reasoning.
            """
        
        result = await self.model.agenerate_with_functions(prompt, [function_spec])
        return json.loads(result)

class TimingMetricsAgent(MetricsAgent):
    """Agent for calculating timing-related process metrics"""
    
    async def analyze(self, df: pd.DataFrame) -> Dict[str, float]:
        # Define function spec for timing analysis
        function_spec = {
            "name": "analyze_timing",
            "description": "Analyze timing patterns in process data",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_columns": {"type": "array", "items": {"type": "string"}},
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "cycle_time": {"type": "number"},
                            "processing_time": {"type": "number"},
                            "waiting_time": {"type": "number"},
                            "throughput": {"type": "number"}
                        }
                    }
                },
                "required": ["time_columns", "metrics"]
            }
        }
        
        # Get datetime columns and calculate initial metrics
        time_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        initial_metrics = {
            "cycle_time": self._calculate_cycle_time(df, time_cols),
            "processing_time": self._calculate_processing_time(df, time_cols),
            "waiting_time": self._calculate_waiting_time(df, time_cols),
            "throughput": self._calculate_throughput(df, time_cols)
        }
        
        # Enhanced RAR prompt for timing analysis
        timing_prompt = """
        Focus on timing metrics:
        1. Current cycle time vs target
        2. Top delay source
        3. Peak load periods
        4. Resource bottlenecks
        Return concise, data-driven insights.
        """
        
        # Prepare context for RAR analysis
        context = {
            "time_columns": time_cols,
            "initial_metrics": initial_metrics,
            "temporal_patterns": self._analyze_temporal_patterns(df, time_cols)
        }
        
        # Get enhanced analysis using RAR
        analysis = await self._execute_analysis(df, function_spec, context, timing_prompt)
        
        # Combine calculated metrics with RAR insights
        return {**initial_metrics, **analysis.get("enhanced_metrics", {})}

    def _analyze_temporal_patterns(self, df: pd.DataFrame, time_cols: List[str]) -> Dict:
        """Analyze temporal patterns in the process"""
        patterns = {}
        for col in time_cols:
            patterns[col] = {
                "hourly_distribution": df[col].dt.hour.value_counts().to_dict(),
                "daily_distribution": df[col].dt.dayofweek.value_counts().to_dict(),
                "monthly_trend": df[col].dt.month.value_counts().to_dict()
            }
        return patterns

    def _calculate_cycle_time(self, df: pd.DataFrame, time_cols: List[str]) -> float:
        """Calculate average cycle time between start and end events"""
        if len(time_cols) >= 2:
            start_col = time_cols[0]
            end_col = time_cols[-1]
            cycle_times = (df[end_col] - df[start_col]).dt.total_seconds() / 3600
            return float(cycle_times.mean())
        return 0.0
    
    def _calculate_processing_time(self, df: pd.DataFrame, time_cols: List[str]) -> float:
        """Calculate actual processing time excluding wait times"""
        total_processing_time = 0.0
        if len(time_cols) > 1:
            for i in range(len(time_cols)-1):
                processing_time = (df[time_cols[i+1]] - df[time_cols[i]]).dt.total_seconds()
                total_processing_time += processing_time.mean()
        return total_processing_time / 3600  # Convert to hours
    
    def _calculate_waiting_time(self, df: pd.DataFrame, time_cols: List[str]) -> float:
        """Calculate total waiting time between process steps"""
        cycle_time = self._calculate_cycle_time(df, time_cols)
        processing_time = self._calculate_processing_time(df, time_cols)
        return max(0, cycle_time - processing_time)
    
    def _calculate_throughput(self, df: pd.DataFrame, time_cols: List[str]) -> float:
        """Calculate process throughput (cases per hour)"""
        if time_cols:
            time_range = (df[time_cols[-1]].max() - df[time_cols[0]].min()).total_seconds() / 3600
            return len(df) / time_range if time_range > 0 else 0
        return 0.0

class QualityMetricsAgent(MetricsAgent):
    """Agent for calculating quality-related process metrics"""
    
    async def analyze(self, df: pd.DataFrame) -> Dict[str, float]:
        # Define function spec for quality analysis
        function_spec = {
            "name": "analyze_quality",
            "description": "Analyze quality indicators in process data",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_patterns": {
                        "type": "object",
                        "properties": {
                            "success_patterns": {"type": "array", "items": {"type": "string"}},
                            "error_patterns": {"type": "array", "items": {"type": "string"}},
                            "rework_patterns": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "first_time_right": {"type": "number"},
                            "error_rate": {"type": "number"},
                            "rework_rate": {"type": "number"},
                            "compliance_rate": {"type": "number"}
                        }
                    }
                },
                "required": ["status_patterns", "metrics"]
            }
        }
        
        # Enhanced RAR prompt for quality analysis
        quality_prompt = """
        Analyze process quality:
        1. Error rate (%)
        2. Most common failure point
        3. Compliance violations
        4. Rework frequency
        Provide specific metrics and causes.
        """
        
        # Calculate initial metrics
        initial_metrics = {
            "first_time_right": self._calculate_first_time_right(df),
            "error_rate": self._calculate_error_rate(df),
            "rework_rate": self._calculate_rework_rate(df),
            "compliance_rate": self._calculate_compliance_rate(df)
        }
        
        # Prepare context for RAR analysis
        context = {
            "initial_metrics": initial_metrics,
            "status_distribution": df['status'].value_counts().to_dict() if 'status' in df.columns else {},
            "quality_indicators": self._analyze_quality_indicators(df)
        }
        
        # Get enhanced analysis using RAR
        analysis = await self._execute_analysis(df, function_spec, context, quality_prompt)
        
        # Combine calculated metrics with RAR insights
        return {**initial_metrics, **analysis.get("enhanced_metrics", {})}

    def _analyze_quality_indicators(self, df: pd.DataFrame) -> Dict:
        """Analyze quality indicators in the process"""
        indicators = {}
        if 'status' in df.columns:
            indicators['status_flow'] = {
                'transitions': df.groupby('status')['status'].shift(-1).value_counts().to_dict(),
                'duration_by_status': df.groupby('status')['duration'].mean().to_dict() if 'duration' in df.columns else {}
            }
        return indicators

    def _calculate_first_time_right(self, df: pd.DataFrame) -> float:
        """Calculate percentage of processes completed correctly on first attempt"""
        if 'status' in df.columns:
            success_count = df[df['status'].str.contains('success|completed|done', case=False, na=False)].shape[0]
            return success_count / len(df)
        return 0.0
    
    def _calculate_error_rate(self, df: pd.DataFrame) -> float:
        """Calculate error rate in process execution"""
        if 'status' in df.columns:
            error_count = df[df['status'].str.contains('error|fail|reject', case=False, na=False)].shape[0]
            return error_count / len(df)
        return 0.0
    
    def _calculate_rework_rate(self, df: pd.DataFrame) -> float:
        """Calculate rate of processes requiring rework"""
        if 'status' in df.columns:
            rework_count = df[df['status'].str.contains('rework|retry|repeat', case=False, na=False)].shape[0]
            return rework_count / len(df)
        return 0.0
    
    def _calculate_compliance_rate(self, df: pd.DataFrame) -> float:
        """Calculate process compliance rate"""
        if 'compliance' in df.columns:
            return df['compliance'].mean()
        return 1.0  # Assume compliant if no compliance column exists

class ResourceMetricsAgent(MetricsAgent):
    """Agent for calculating resource utilization metrics"""
    
    async def analyze(self, df: pd.DataFrame) -> Dict[str, float]:
        # Define function spec for resource analysis
        function_spec = {
            "name": "analyze_resources",
            "description": "Analyze resource utilization and efficiency",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_analysis": {
                        "type": "object",
                        "properties": {
                            "utilization": {"type": "number"},
                            "workload_distribution": {"type": "number"},
                            "efficiency": {"type": "number"},
                            "bottleneck_score": {"type": "number"}
                        }
                    },
                    "optimization_suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "resource": {"type": "string"},
                                "issue": {"type": "string"},
                                "impact": {"type": "number"},
                                "suggestion": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["resource_analysis", "optimization_suggestions"]
            }
        }
        
        # Enhanced RAR prompt for resource analysis
        resource_prompt = """
        Analyze resource utilization:
        1. Underutilized resources (< 70%)
        2. Overloaded resources (> 90%)
        3. Workload imbalances
        4. Resource cost efficiency
        Return concrete numbers and specific resources.
        """
        
        # Calculate initial metrics
        initial_metrics = {
            "resource_utilization": self._calculate_resource_utilization(df),
            "workload_distribution": self._calculate_workload_distribution(df),
            "resource_efficiency": self._calculate_resource_efficiency(df),
            "bottleneck_score": self._calculate_bottleneck_score(df)
        }
        
        # Prepare context for RAR analysis
        context = {
            "initial_metrics": initial_metrics,
            "resource_patterns": self._analyze_resource_patterns(df)
        }
        
        # Get enhanced analysis using RAR with specific resource focus
        analysis = await self._execute_analysis(df, function_spec, context, resource_prompt)
        
        # Store optimization suggestions for immediate action
        if "optimization_suggestions" in analysis:
            self._store_optimization_suggestions(analysis["optimization_suggestions"])
            
        return {**initial_metrics, **analysis.get("resource_analysis", {})}

    def _analyze_resource_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze resource utilization patterns"""
        patterns = {}
        if 'resource' in df.columns:
            patterns['resource_load'] = {
                'by_time': df.groupby(['resource', pd.Grouper(key='timestamp', freq='H')])['duration'].sum().to_dict() 
                          if 'timestamp' in df.columns and 'duration' in df.columns else {},
                'by_task_type': df.groupby(['resource', 'task_type']).size().to_dict() 
                               if 'task_type' in df.columns else {}
            }
        return patterns

    def _store_optimization_suggestions(self, suggestions: List[Dict]):
        """Store optimization suggestions for later use"""
        # This would typically store in a database or memory system
        self.optimization_suggestions = suggestions

    def _calculate_resource_utilization(self, df: pd.DataFrame) -> float:
        """Calculate overall resource utilization rate"""
        if 'resource' in df.columns and 'duration' in df.columns:
            total_time = df['duration'].sum()
            resource_times = df.groupby('resource')['duration'].sum()
            return float(resource_times.mean() / total_time if total_time > 0 else 0)
        return 0.0
    
    def _calculate_workload_distribution(self, df: pd.DataFrame) -> float:
        """Calculate evenness of workload distribution across resources"""
        if 'resource' in df.columns:
            resource_counts = df['resource'].value_counts()
            if len(resource_counts) > 0:
                std_dev = resource_counts.std()
                mean = resource_counts.mean()
                return 1 - (std_dev / mean if mean > 0 else 0)  # Higher score means more even distribution
        return 0.0
    
    def _calculate_resource_efficiency(self, df: pd.DataFrame) -> float:
        """Calculate resource efficiency based on output vs time spent"""
        if 'resource' in df.columns and 'duration' in df.columns and 'output' in df.columns:
            efficiency = (df['output'] / df['duration']).mean()
            return float(efficiency)
        return 0.0
    
    def _calculate_bottleneck_score(self, df: pd.DataFrame) -> float:
        """Calculate bottleneck score based on resource wait times"""
        if 'wait_time' in df.columns:
            total_wait_time = df['wait_time'].sum()
            total_time = df['duration'].sum() if 'duration' in df.columns else 1
            return float(1 - (total_wait_time / total_time if total_time > 0 else 0))
        return 1.0

# Helper function to initialize metrics agents
def create_metrics_agents(model: WatsonxLLM) -> Dict[str, MetricsAgent]:
    """Create and return initialized metrics agents"""
    return {
        "timing": TimingMetricsAgent(model=model, tools=[]),
        "quality": QualityMetricsAgent(model=model, tools=[]),
        "resource": ResourceMetricsAgent(model=model, tools=[])
    }