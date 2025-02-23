"""
Efficient ticket processing with functional patterns
"""
from typing import Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
import pandas as pd
import logging
from datetime import datetime
from functools import reduce

logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """Configuration for ticket processing"""
    # Optional columns that will be processed if present
    optional_columns: Set[str] = field(default_factory=lambda: {
        'subject', 'body', 'type', 'priority', 'language'
    })
    # Time-related columns - will process any that match common patterns
    time_columns: Set[str] = field(default_factory=lambda: {
        'created_at', 'updated_at', 'resolved_at', 'timestamp', 'date'
    })
    # Categorical columns to convert
    categorical_columns: Set[str] = field(default_factory=lambda: {
        'type', 'priority', 'status', 'language', 'category', 'department'
    })

class TicketProcessor:
    """Functional ticket processor implementation"""
    
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self._transformers: List[Callable] = [
            self._preprocess_timestamps,
            self._preprocess_categories,
            self._detect_columns
        ]
    
    def _detect_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and categorize available columns"""
        # Find time-like columns using pandas dtype detection
        time_cols = df.select_dtypes(include=['datetime64']).columns
        self.config.time_columns.update(time_cols)
        
        # Find categorical-like columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        self.config.categorical_columns.update(
            col for col in cat_cols 
            if df[col].nunique() < df.shape[0] * 0.05  # Less than 5% unique values
        )
        
        return df
    
    def process_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process dataset through transformation pipeline"""
        try:
            # Apply all transformers
            processed_df = reduce(
                lambda acc, transformer: transformer(acc), 
                self._transformers, 
                df.copy()
            )
            
            return {
                "metadata": self._extract_metadata(processed_df),
                "metrics": self._calculate_metrics(processed_df),
                "patterns": self._identify_patterns(processed_df),
                "data_quality": self._assess_data_quality(processed_df)
            }
            
        except Exception as e:
            logger.error(f"Dataset processing failed: {e}")
            raise

    def _preprocess_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert timestamp columns efficiently"""
        # Try to detect additional datetime columns
        for col in df.columns:
            if any(time_hint in col.lower() for time_hint in ['date', 'time', 'created', 'updated', 'timestamp']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    self.config.time_columns.add(col)
                except:
                    continue
        
        # Process known time columns
        for col in self.config.time_columns & set(df.columns):
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df

    def _preprocess_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert categorical columns efficiently"""
        present_cats = self.config.categorical_columns & set(df.columns)
        for col in present_cats:
            if df[col].nunique() < df.shape[0] * 0.05:  # Only if relatively few unique values
                df[col] = df[col].astype('category')
        return df

    def _extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract dataset metadata efficiently"""
        time_cols = self.config.time_columns & set(df.columns)
        earliest_time = None
        latest_time = None
        
        for col in time_cols:
            if not df[col].isna().all():
                col_min = df[col].min()
                col_max = df[col].max()
                if earliest_time is None or col_min < earliest_time:
                    earliest_time = col_min
                if latest_time is None or col_max > latest_time:
                    latest_time = col_max
        
        return {
            "total_records": len(df),
            "columns": list(df.columns),
            "time_range": {
                "start": earliest_time.isoformat() if earliest_time else None,
                "end": latest_time.isoformat() if latest_time else None
            } if earliest_time and latest_time else {},
            "categories": {
                col: df[col].value_counts().to_dict()
                for col in self.config.categorical_columns & set(df.columns)
            }
        }

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate metrics efficiently using vectorized operations"""
        metrics = {}
        
        # Time-based metrics
        time_cols = sorted(self.config.time_columns & set(df.columns))
        if len(time_cols) >= 2:
            for start, end in zip(time_cols[:-1], time_cols[1:]):
                duration = (df[end] - df[start]).dt.total_seconds()
                metrics[f"{start}_to_{end}"] = {
                    "mean": duration.mean(),
                    "median": duration.median(),
                    "p95": duration.quantile(0.95)
                }
        
        # Categorical metrics
        cat_cols = self.config.categorical_columns & set(df.columns)
        if cat_cols:
            metrics["distributions"] = {
                col: df[col].value_counts(normalize=True).to_dict()
                for col in cat_cols
            }
        
        return metrics

    def _identify_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify patterns using vectorized operations"""
        patterns = []
        
        # Temporal patterns
        time_cols = self.config.time_columns & set(df.columns)
        for col in time_cols:
            if not df[col].isna().all():
                patterns.extend([
                    {
                        "type": "temporal",
                        "subtype": "daily",
                        "field": col,
                        "distribution": df[col].dt.day_name().value_counts().to_dict()
                    },
                    {
                        "type": "temporal",
                        "subtype": "hourly",
                        "field": col,
                        "distribution": df[col].dt.hour.value_counts().sort_index().to_dict()
                    }
                ])
        
        # Categorical patterns
        cat_cols = list(self.config.categorical_columns & set(df.columns))
        for i, col1 in enumerate(cat_cols):
            for col2 in cat_cols[i+1:]:
                cross_tab = pd.crosstab(df[col1], df[col2], normalize='all')
                patterns.append({
                    "type": "categorical",
                    "fields": [col1, col2],
                    "distribution": cross_tab.to_dict()
                })
        
        return patterns

    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Check completeness for all columns
        completeness = {
            col: float(df[col].notna().mean())
            for col in df.columns
        }
        
        # Calculate field statistics
        field_stats = {
            col: {
                "unique_values": int(df[col].nunique()),
                "missing_values": int(df[col].isna().sum()),
                "top_values": df[col].value_counts().head(5).to_dict()
            }
            for col in df.columns
        }
        
        # Generate warnings
        warnings = []
        
        # Check for high missing values
        for col, missing_rate in df.isna().mean().items():
            if missing_rate > 0.1:  # Warning threshold for missing values
                warnings.append({
                    "type": "high_missing_values",
                    "field": col,
                    "missing_rate": float(missing_rate)
                })
        
        # Check optional columns presence
        missing_recommended = self.config.optional_columns - set(df.columns)
        if missing_recommended:
            warnings.append({
                "type": "missing_recommended_columns",
                "fields": list(missing_recommended),
                "impact": "Some recommended columns are missing, which may limit analysis capabilities"
            })
        
        # Check timestamp columns
        time_cols = set(df.columns) & self.config.time_columns
        if not time_cols:
            warnings.append({
                "type": "no_timestamp_columns",
                "impact": "No timestamp columns detected, temporal analysis will be limited"
            })
        
        # Check categorical columns quality
        for col in (set(df.columns) & self.config.categorical_columns):
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio > 0.5:  # More than 50% unique values
                warnings.append({
                    "type": "high_cardinality_categorical",
                    "field": col,
                    "unique_ratio": float(unique_ratio),
                    "impact": "Column marked as categorical but has high cardinality"
                })
        
        return {
            "completeness": completeness,
            "field_stats": field_stats,
            "warnings": warnings,
            "analyzed_columns": {
                "temporal": list(time_cols),
                "categorical": list(set(df.columns) & self.config.categorical_columns),
                "total_columns": len(df.columns)
            }
        }