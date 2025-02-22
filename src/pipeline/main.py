import logging
import pandas as pd
from typing import Dict, Any, Optional
from langchain_ibm import WatsonxLLM
from ..agents.processlens_agent import ProcessLensAgent
from .analysis_pipeline import AnalysisPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_analysis(
    dataset_path: str, 
    model_params: dict,
    timeout: Optional[int] = 300,
    business_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Enhanced analysis entry point with function calling support"""
    try:
        # Initialize model with default parameters if not specified
        default_params = {
            "temperature": 0.7,
            "max_new_tokens": 1000,
            "min_new_tokens": 1,
            "repetition_penalty": 1.1,
            "decoding_method": "greedy"
        }
        model_params = {**default_params, **model_params}
        
        # Initialize model
        model = WatsonxLLM(**model_params)
        logger.info("Initialized WatsonxLLM model")

        # Create agent with custom timeout
        agent = ProcessLensAgent(llm=model, tools=[])
        agent.timeout = timeout if timeout else 300
        
        # Initialize pipeline with function calling support
        pipeline = AnalysisPipeline(agent, model_params)
        logger.info("Starting process analysis with function calling support...")

        # Load and validate dataset 
        df = pd.read_csv(dataset_path)
        if df.empty:
            raise ValueError("Dataset is empty")
            
        # Run analysis
        results = await pipeline.analyze_dataset(df)
        
        # Add business context processing
        if business_context:
            logger.info("Processing with business context...")
            results["business_context"] = business_context
            
        # Enhanced results structure with function calling insights
        results = {
            "status": "success",
            "progress": pipeline.progress,
            "summary": {
                "key_findings": results.get("structure", {}).get("kpi_analysis", {}),
                "critical_metrics": results.get("patterns", {}).get("efficiency_analysis", {}),
                "action_items": results.get("optimizations", {})
            },
            "details": results
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "status": "error",
            "progress": -1,
            "error": str(e)
        }
