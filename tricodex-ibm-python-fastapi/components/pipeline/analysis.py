"""
Enhanced analysis module with functional programming patterns
"""
from typing import Dict, Any, Optional, List, Callable
from functools import partial, reduce
import logging
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from utils.helpers import ProcessLensError

logger = logging.getLogger(__name__)

@dataclass
class AnalysisMetric:
    """Analysis metric with contextual information"""
    name: str
    value: float
    context: Dict[str, Any]
    confidence: float
    timestamp: datetime = datetime.now()

class Analysis:
    """Functional analysis implementation"""
    
    def __init__(self):
        self.metrics: List[AnalysisMetric] = []
        self.transformers: List[Callable] = []
    
    def pipe(self, transformer: Callable) -> 'Analysis':
        """Add a transformer to the analysis pipeline"""
        self.transformers.append(transformer)
        return self
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis pipeline"""
        try:
            # Apply transformers in sequence
            result = reduce(
                lambda acc, transformer: transformer(acc),
                self.transformers,
                data
            )
            
            return self._structure_results(result)
            
        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            raise ProcessLensError(f"Analysis execution failed: {str(e)}")
    
    @staticmethod
    def _structure_results(data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure analysis results"""
        return {
            "metrics": data.get("metrics", {}),
            "patterns": data.get("patterns", []),
            "insights": data.get("insights", []),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.0",
                "status": "success"
            }
        }

# Predefined transformers
def analyze_temporal_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze temporal patterns in data"""
    df = data.get("dataframe")
    if not isinstance(df, pd.DataFrame):
        return data
        
    time_cols = df.select_dtypes(include=['datetime64']).columns
    
    patterns = []
    for col in time_cols:
        # Daily patterns
        daily = df[col].dt.day_name().value_counts()
        patterns.append({
            "type": "temporal",
            "subtype": "daily",
            "column": col,
            "distribution": daily.to_dict()
        })
        
        # Hourly patterns
        hourly = df[col].dt.hour.value_counts().sort_index()
        patterns.append({
            "type": "temporal",
            "subtype": "hourly",
            "column": col,
            "distribution": hourly.to_dict()
        })
    
    data["temporal_patterns"] = patterns
    return data

def analyze_categorical_correlations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze correlations between categorical variables"""
    df = data.get("dataframe")
    if not isinstance(df, pd.DataFrame):
        return data
        
    cat_cols = df.select_dtypes(include=['category', 'object']).columns
    
    correlations = []
    for col1 in cat_cols:
        for col2 in cat_cols:
            if col1 < col2:  # Avoid duplicate combinations
                matrix = pd.crosstab(df[col1], df[col2], normalize='all')
                correlations.append({
                    "type": "categorical_correlation",
                    "columns": [col1, col2],
                    "matrix": matrix.to_dict()
                })
    
    data["categorical_correlations"] = correlations
    return data

def analyze_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate key process metrics"""
    df = data.get("dataframe")
    if not isinstance(df, pd.DataFrame):
        return data
        
    metrics = {}
    
    # Time-based metrics
    time_cols = df.select_dtypes(include=['datetime64']).columns
    if len(time_cols) >= 2:
        metrics["processing_time"] = (
            df[time_cols[-1]] - df[time_cols[0]]
        ).dt.total_seconds().agg(['mean', 'median', 'std']).to_dict()
    
    # Categorical metrics
    cat_cols = df.select_dtypes(include=['category', 'object']).columns
    for col in cat_cols:
        metrics[f"{col}_distribution"] = df[col].value_counts(normalize=True).to_dict()
    
    data["metrics"] = metrics
    return data

def analyze_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze data quality metrics"""
    df = data.get("dataframe")
    if not isinstance(df, pd.DataFrame):
        return data
        
    quality = {
        "completeness": df.notna().mean().to_dict(),
        "unique_values": df.nunique().to_dict(),
        "warnings": []
    }
    
    # Check for potential issues
    for col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            quality["warnings"].append({
                "type": "missing_values",
                "column": col,
                "count": int(missing)
            })
    
    data["data_quality"] = quality
    return data

# Create analysis pipeline
def create_analysis_pipeline() -> Analysis:
    """Create a preconfigured analysis pipeline"""
    return (Analysis()
            .pipe(analyze_temporal_patterns)
            .pipe(analyze_categorical_correlations)
            .pipe(analyze_metrics)
            .pipe(analyze_data_quality))
