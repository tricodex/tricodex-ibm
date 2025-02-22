"""
ProcessLens: Universal Process Mining Framework
Core implementation using RAR (Retrieval-Augmented Reasoning) with IBM Granite
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from langchain_ibm import WatsonxLLM
from pipeline import create_metrics_agents
import networkx as nx
import asyncio
import json
import logging
import os
import re

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ProcessStep:
    """Represents a single step in a business process."""
    id: str
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]
    actors: List[str]
    duration: Optional[float]
    frequency: Optional[int]

@dataclass
class ProcessPattern:
    """Represents a recurring pattern in the process."""
    name: str
    steps: List[ProcessStep]  # Fixed: Changed List<ProcessStep> to List[ProcessStep]
    frequency: int
    performance_metrics: Dict[str, float]
    context: Dict[str, Any]

class DatasetAnalyzer:
    """Analyzes dataset structure and content using RAR."""
    
    def __init__(self, granite_model: WatsonxLLM):
        self.model = granite_model
        self.known_patterns = {}
        
    async def analyze_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze dataset structure using RAR."""
        try:
            # Create dataset description for RAR
            dataset_info = {
                "columns": list(df.columns),
                "sample_data": df.head(5).to_dict('records'),
                "data_types": df.dtypes.apply(lambda dt: dt.name).to_dict(),
                "null_counts": df.isnull().sum().to_dict()
            }
            
            logger.info(f"Analyzing structure for dataset with {len(df.columns)} columns")
            
            # Simplified prompt for better model responses
            structure_prompt = f"""
            Given this dataset information, identify the role of each column and provide analysis results in valid JSON format.
            Focus on these column types:
            1. Process steps/activities
            2. Timestamps
            3. Actors/resources
            4. Status fields
            5. Input/output fields

            Dataset columns and sample:
            {json.dumps(dataset_info, indent=2)}

            Format your response as a JSON object with this structure:
            {{
                "process_entities": ["column1", "column2"],
                "temporal_columns": ["timestamp1"],
                "actor_columns": ["actor1"],
                "status_columns": ["status1"],
                "io_columns": ["input1", "output1"]
            }}
            """
            
            # Get model response
            logger.info("Sending structure analysis prompt to model")
            response = await self.model.ainvoke(structure_prompt)
            
            # Debug log the raw response
            logger.info(f"Raw model response: {response}")
            
            # Extract content from response
            if isinstance(response, str):
                raw_analysis = response
            else:
                # Handle structured response object
                raw_analysis = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"Processed model response: {raw_analysis}")
            
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', raw_analysis)
            if json_match:
                json_str = json_match.group(0)
                try:
                    analysis = json.loads(json_str)
                    logger.info(f"Successfully parsed structure analysis: {json.dumps(analysis, indent=2)}")
                    return analysis
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from model response: {e}")
                    logger.error(f"JSON string attempted to parse: {json_str}")
                    # Return a default structure if JSON parsing fails
                    return {
                        "process_entities": [],
                        "temporal_columns": [],
                        "actor_columns": [],
                        "status_columns": [],
                        "io_columns": []
                    }
            else:
                logger.error("No JSON found in model response")
                # Return a default structure if no JSON found
                return {
                    "process_entities": [],
                    "temporal_columns": [],
                    "actor_columns": [],
                    "status_columns": [],
                    "io_columns": []
                }
                
        except Exception as e:
            logger.error(f"Error in analyze_structure: {str(e)}")
            raise
    
    async def analyze_structure_with_functions(self, df: pd.DataFrame, functions_list: list) -> Dict[str, Any]:
        """Analyze dataset structure using RAR with function calling."""
        dataset_info = {
            "columns": list(df.columns),
            "sample_data": df.head(5).to_dict('records'),
            "data_types": df.dtypes.apply(lambda dt: dt.name).to_dict(),
            "null_counts": df.isnull().sum().to_dict()
        }
        structure_prompt = f"""
        Analyze this dataset structure and identify key process-related components along with roles for each column.

        Dataset Information:
        {json.dumps(dataset_info, indent=2)}

        Return the analysis in structured JSON format.
        """
        analysis = await self.model.agenerate_with_functions(structure_prompt, functions_list)
        return json.loads(analysis)

class ProcessMiner:
    """Mines process patterns and flows using RAR."""
    
    def __init__(self, granite_model: WatsonxLLM):
        self.model = granite_model
        self.graph = nx.DiGraph()
        
    async def extract_process_steps(self, 
                                  df: pd.DataFrame, 
                                  structure: Dict[str, Any]) -> List[ProcessStep]:
        """Extract process steps from the dataset."""
        
        # Prepare context for RAR
        process_context = {
            "structure": structure,
            "sample_flows": df.head(10).to_dict('records'),
            "unique_values": {
                col: df[col].unique().tolist()[:10] 
                for col in df.columns
            },
            "transitions": self._analyze_transitions(df, structure)
        }
        
        # RAR prompt for process step extraction
        steps_prompt = f"""
        Based on the process context below, identify:
        1. Distinct process steps with clear entry and exit criteria
        2. Required inputs and outputs for each step
        3. Actors involved in each step
        4. Typical duration and frequency of each step
        5. Dependencies between steps
        6. Decision points and conditions

        Process Context:
        {json.dumps(process_context, indent=2)}

        Return detailed step definitions in JSON format that can be mapped
        to ProcessStep objects.
        """
        
        # Get RAR analysis
        steps_analysis = await self.model.agenerate(steps_prompt)
        
        # Parse and convert to ProcessStep objects
        steps_data = json.loads(steps_analysis)
        steps = [ProcessStep(**step) for step in steps_data]
        
        return steps
    
    def _analyze_transitions(self, 
                           df: pd.DataFrame, 
                           structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze state transitions in the process."""
        transitions = {}
        
        # Identify state/status columns from structure
        state_columns = [
            col for col in structure 
            if isinstance(structure.get(col), dict) and structure[col].get('type') == 'state'
        ]
        
        for col in state_columns:
            transitions[col] = {
                "matrix": pd.crosstab(
                    df[col], 
                    df[col].shift(-1)
                ).to_dict(),
                "frequencies": df[col].value_counts().to_dict()
            }
            
        return transitions
    
    async def identify_patterns(self, steps: List[ProcessStep]) -> List[ProcessPattern]:
        """Identify process patterns from extracted steps."""
        patterns_dict = {}
        for step in steps:
            if step.name in patterns_dict:
                patterns_dict[step.name].append(step)
            else:
                patterns_dict[step.name] = [step]
        patterns = []
        for name, steps_group in patterns_dict.items():
            pattern = ProcessPattern(
                name=name,
                steps=steps_group,
                frequency=len(steps_group),
                performance_metrics={},
                context={}
            )
            patterns.append(pattern)
        return patterns

class ProcessOptimizer:
    """Generates process improvements using RAR."""
    
    def __init__(self, granite_model: WatsonxLLM):
        self.model = granite_model
        self.metrics_agents = create_metrics_agents(granite_model)
        
    async def analyze_performance(self, 
                                patterns: List[ProcessPattern],
                                process_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze process performance and identify improvement areas."""
        
        # Calculate performance metrics using specialized agents
        timing_metrics = await self.metrics_agents["timing"].analyze(process_data)
        quality_metrics = await self.metrics_agents["quality"].analyze(process_data)
        resource_metrics = await self.metrics_agents["resource"].analyze(process_data)
        
        performance_metrics = {
            'timing': timing_metrics,
            'quality': quality_metrics,
            'resources': resource_metrics
        }
        
        # Prepare analysis context
        analysis_context = {
            "patterns": [pattern.__dict__ for pattern in patterns],
            "metrics": performance_metrics,
            "historical_performance": self._get_historical_performance(process_data)
        }
        
        # Define function calling schema for process analysis
        analyze_function = {
            "name": "analyze_process_performance",
            "description": "Analyze process performance metrics and identify improvements",
            "parameters": {
                "type": "object",
                "properties": {
                    "critical_metrics": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "improvement_areas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "area": {"type": "string"},
                                "impact": {"type": "number"},
                                "suggestion": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        
        analysis_prompt = f"""
        Based on the process performance data below, identify:
        1. Critical bottlenecks and their root causes
        2. Inefficient patterns and their impact
        3. Resource utilization issues
        4. Quality and compliance risks
        5. High-impact improvement opportunities
        
        Analysis Context:
        {json.dumps(analysis_context, indent=2)}
        
        Provide a detailed analysis in JSON format with:
        - Specific issues identified
        - Supporting metrics and evidence
        - Impact assessment
        - Priority ranking
        """
        
        analysis = await self.model.agenerate_with_functions(
            analysis_prompt,
            [analyze_function]
        )
        
        return json.loads(analysis)
    
    def _get_historical_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get historical performance metrics."""
        if df.empty:
            return {}
            
        timestamp_cols = df.select_dtypes(include=['datetime64']).columns
        if len(timestamp_cols) > 0:
            df['period'] = pd.to_datetime(df[timestamp_cols[0]]).dt.to_period('M')
            historical_metrics = df.groupby('period').agg({
                'duration': ['mean', 'std'],
                'status': lambda x: (x == 'completed').mean() if 'status' in df.columns else None,
                'resource': 'nunique'
            }).to_dict()
            return historical_metrics
            
        return {}
    
    async def generate_improvements(self, performance: dict, patterns: List[ProcessPattern], process_characteristics: dict) -> Dict[str, Any]:
        """Generate improvement recommendations based on performance, patterns, and characteristics."""
        prompt = f"""
        As a process optimization expert, analyze these metrics and provide 3 improvements:
        1. Highest ROI improvement (quantify impact)
        2. Quickest to implement (under 30 days)
        3. Most critical bottleneck fix
        
        For each improvement:
        - Exact steps to implement
        - Expected ROI percentage
        - Implementation timeline
        - Required resources
        
        Performance data:
        {json.dumps(performance, indent=2)}
        
        Return in JSON format with numerical metrics.
        """
        improvements = await self.model.agenerate(prompt)
        return json.loads(improvements)

class ProcessLens:
    """Main class coordinating process analysis and optimization."""
    
    def __init__(self, granite_model: WatsonxLLM):
        self.model = granite_model
        self.analyzer = DatasetAnalyzer(granite_model)
        self.miner = ProcessMiner(granite_model)
        self.optimizer = ProcessOptimizer(granite_model)
        
    async def analyze_dataset(self, df: pd.DataFrame, thought_callback=None) -> Dict[str, Any]:
        """Analyze a process dataset using RAR with thought tracking."""
        try:
            logger.info("Starting dataset analysis with ProcessLens...")
            
            # Get structure analysis
            logger.info("Analyzing dataset structure...")
            structure = await self.analyzer.analyze_structure(df)
            
            if thought_callback:
                first_thought = f"Dataset loaded successfully. Analyzing {len(df.columns)} columns and {len(df)} rows to identify process elements."
                await thought_callback(
                    "structure_analysis",
                    first_thought
                )
                
            logger.info(f"Structure analysis complete: {json.dumps(structure, indent=2)}")
            
            if thought_callback:
                process_entities = len(structure.get('process_entities', []))
                temporal_cols = len(structure.get('temporal_columns', []))
                await thought_callback(
                    "structure_analysis",
                    f"Identified {process_entities} process entities and {temporal_cols} temporal dimensions. Starting pattern analysis."
                )
            
            # Extract process steps with progress updates
            logger.info("Extracting process steps...")
            if thought_callback:
                await thought_callback(
                    "pattern_mining",
                    "Starting process step extraction and pattern analysis..."
                )
                
            steps = await self.miner.extract_process_steps(df, structure)
            logger.info(f"Extracted {len(steps)} process steps")
            
            if thought_callback:
                await thought_callback(
                    "pattern_mining",
                    f"Discovered {len(steps)} distinct process steps. Analyzing execution patterns and flow dependencies."
                )
            
            # Identify patterns with detailed logging
            logger.info("Identifying process patterns...")
            patterns = await self.miner.identify_patterns(steps)
            logger.info(f"Identified {len(patterns)} patterns")
            
            if thought_callback:
                pattern_names = [p.name for p in patterns]
                await thought_callback(
                    "performance_analysis",
                    f"Found {len(patterns)} process patterns: {', '.join(pattern_names[:3])}... Calculating performance metrics."
                )
            
            # Return serialized results
            results = {
                "structure": structure,
                "patterns": [pattern.__dict__ for pattern in patterns],
                "performance": {},
                "improvements": []
            }
            
            logger.info("Analysis completed successfully")
            return serialize_dates(results)
            
        except Exception as e:
            logger.error(f"Error in process analysis: {str(e)}")
            if thought_callback:
                await thought_callback(
                    "error",
                    f"Analysis encountered an error: {str(e)}"
                )
            raise

# Helper function to handle datetime serialization
def serialize_dates(obj):
    """Convert any datetime objects to ISO format strings"""
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(item) for item in obj]
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    return obj

# Example usage
async def main():
    """Example usage of ProcessLens with IBM Granite"""
    try:
        model = WatsonxLLM(
            model_id="ibm/granite-3-8b-instruct",
            url=os.getenv("WATSONX_URL"),
            apikey=os.getenv("IBM_API_KEY"),
            project_id=os.getenv("PROJECT_ID")
        )
        
        # Initialize ProcessLens
        process_lens = ProcessLens(model)
        
        # Load example dataset
        df = pd.read_csv("customer_support_tickets.csv")
        
        # Analyze process
        results = await process_lens.analyze_dataset(df)
        
        # Print results
        print(json.dumps(results, indent=2))

    except Exception as e:
        logger.error(f"Error in ProcessLens example: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())