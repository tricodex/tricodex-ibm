import logging
import pandas as pd
from langchain_ibm import WatsonxLLM
from ..agents.processlens_agent import ProcessLensAgent
from .analysis_pipeline import AnalysisPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_analysis(dataset_path: str, model_params: dict) -> dict:
    """
    Main entry point for running the process analysis
    """
    try:
        # Initialize model
        model = WatsonxLLM(**model_params)
        logger.info("Initialized WatsonxLLM model")

        # Create agent 
        agent = ProcessLensAgent(llm=model, tools=[])
        
        # Initialize pipeline
        pipeline = AnalysisPipeline(agent)
        logger.info("Starting process analysis...")

        # Load dataset
        df = pd.read_csv(dataset_path)
        
        # Run analysis
        results = await pipeline.analyze_dataset(df)
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
