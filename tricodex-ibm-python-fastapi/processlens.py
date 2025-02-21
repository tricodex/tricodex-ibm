"""
ProcessLens: Universal Process Mining Framework
Core implementation using RAR (Retrieval-Augmented Reasoning) with IBM Granite
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langchain_ibm import WatsonxLLM
import asyncio
import json
from pipeline import create_metrics_agents

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
    steps: List[ProcessStep]
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
        
        # Create dataset description for RAR
        dataset_info = {
            "columns": list(df.columns),
            "sample_data": df.head(5).to_dict('records'),
            "data_types": df.dtypes.apply(lambda dt: dt.name).to_dict(),
            "null_counts": df.isnull().sum().to_dict()
        }
        
        # RAR prompt for structure analysis
        structure_prompt = f"""
        Analyze this dataset structure and identify:
        1. Key process-related columns
        2. Temporal columns
        3. Actor/agent columns
        4. Status/state columns
        5. Input/output columns

        Dataset Information:
        {json.dumps(dataset_info, indent=2)}

        Return the analysis in a structured JSON format identifying the role of each column
        and explaining your reasoning for the classification.
        """
        
        # Get RAR analysis
        analysis = await self.model.agenerate(structure_prompt)
        
        # Parse and return structure analysis
        return json.loads(analysis)
    
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
        """Complete analysis of a process dataset using RAR with thought tracking."""
        
        # Helper to capture model thoughts with optimized prompts and refinement
        async def get_model_thought(stage: str, max_retries: int = 2) -> str:
            prompts = {
                "structure_analysis": "What is the key process entity and its main relationships? Focus on the most important data column.",
                
                "pattern_mining": "What is the most frequent process pattern and its direct business impact? Give exact numbers.",
                
                "performance_analysis": "What is the biggest bottleneck and its percentage impact on efficiency? Be specific.",
                
                "improvement_generation": "What single improvement would give the highest ROI? State exact percentage.",
                
                "final_synthesis": "List top 3 findings with numerical metrics. Format: 1. Metric: value - impact"
            }
            
            for attempt in range(max_retries):
                thought = await self.model.agenerate(
                    f"You are a process mining expert. {prompts[stage]} Answer in exactly one sentence with concrete numbers."
                )
                thought = thought.strip()
                
                # Validate thought quality
                if (
                    len(thought.split()) <= 30 and 
                    any(char.isdigit() for char in thought) and 
                    thought.endswith((".", "!", "%"))
                ):
                    return thought
                    
                # If invalid, try one more time with more explicit instructions
                if attempt == 0:
                    thought = await self.model.agenerate(
                        f"Revise this unclear insight: '{thought}'\nMake it one sentence with exact numbers and metrics."
                    )
            
            # If still not good after retries, return a formatted version of best attempt
            return f"{thought.split('.')[0].strip()}."
        
        # 1. Analyze dataset structure with function calling
        if thought_callback:
            thought = await get_model_thought("structure_analysis")
            thought_callback("structure_analysis", thought)
            
        structure = await self.analyzer.analyze_structure_with_functions(df, [dataset_analysis_spec])
        
        # 2. Extract and analyze process patterns
        if thought_callback:
            thought = await get_model_thought("pattern_mining")
            thought_callback("pattern_mining", thought)
            
        steps = await self.miner.extract_process_steps(df, structure)
        patterns = await self.miner.identify_patterns(steps)
        
        # 3. Perform RAR-enhanced performance analysis
        if thought_callback:
            thought = await get_model_thought("performance_analysis")
            thought_callback("performance_analysis", thought)
            
        performance = await self.optimizer.analyze_performance(patterns, df)
        
        # 4. Generate context-aware improvements
        if thought_callback:
            thought = await get_model_thought("improvement_generation")
            thought_callback("improvement_generation", thought)
            
        improvements = await self.optimizer.generate_improvements(
            performance, 
            patterns,
            structure.get("process_characteristics", {})
        )
        
        # 5. Synthesize final analysis
        if thought_callback:
            thought = await get_model_thought("final_synthesis")
            thought_callback("final_synthesis", thought)
        
        synthesis = await self.model.agenerate_with_functions(
            json.dumps({
                "structure": structure,
                "patterns": [pattern.__dict__ for pattern in patterns],
                "performance": performance,
                "improvements": improvements
            }),
            [synthesis_spec]
        )
        
        return {
            "structure": structure,
            "patterns": [pattern.__dict__ for pattern in patterns],
            "performance": performance,
            "improvements": improvements,
            "synthesis": json.loads(synthesis)
        }

# Example usage
async def main():
    # Initialize IBM Granite model
    model_parameters = {
        "decoding_method": "greedy",
        "max_new_tokens": 1000,
        "min_new_tokens": 1,
        "temperature": 0.7,
    }
    
    model = WatsonxLLM(
        model_id="ibm/granite-3-8b-instruct",
        credentials={
            "url": "YOUR_URL",
            "apikey": "YOUR_API_KEY"
        },
        project_id="YOUR_PROJECT_ID",
        params=model_parameters
    )
    
    # Initialize ProcessLens
    process_lens = ProcessLens(model)
    
    # Load example dataset
    df = pd.read_csv("customer_support_tickets.csv")
    
    # Analyze process
    results = await process_lens.analyze_dataset(df)
    
    # Print results
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())