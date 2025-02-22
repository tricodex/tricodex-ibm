import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TicketProcessor:
    """Processes and analyzes ticket datasets"""
    
    def __init__(self):
        self.required_columns = ['subject', 'body', 'type', 'priority', 'language']

    def process_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process ticket dataset and extract key metrics"""
        try:
            # Validate and standardize columns
            available_columns = set(df.columns)
            metadata = {
                "total_tickets": len(df),
                "available_fields": list(available_columns),
                "languages": df['language'].unique().tolist() if 'language' in df.columns else [],
                "ticket_types": df['type'].unique().tolist() if 'type' in df.columns else [],
                "priorities": df['priority'].unique().tolist() if 'priority' in df.columns else []
            }
            
            # Extract basic metrics
            metrics = self._calculate_metrics(df)
            
            # Identify patterns
            patterns = self._identify_patterns(df)

            return {
                "metadata": metadata,
                "metrics": metrics,
                "patterns": patterns,
                "data_quality": self._assess_data_quality(df)
            }

        except Exception as e:
            logger.error(f"Error processing dataset: {e}")
            raise

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate key metrics from ticket data"""
        metrics = {}
        
        if 'priority' in df.columns:
            metrics['priority_distribution'] = df['priority'].value_counts().to_dict()
            
        if 'type' in df.columns:
            metrics['type_distribution'] = df['type'].value_counts().to_dict()
            
        if 'language' in df.columns:
            metrics['language_distribution'] = df['language'].value_counts().to_dict()

        return metrics

    def _identify_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify patterns in ticket data"""
        patterns = []
        
        if 'type' in df.columns and 'priority' in df.columns:
            type_priority_correlation = df.groupby(['type', 'priority']).size().unstack()
            patterns.append({
                "name": "type_priority_correlation",
                "description": "Correlation between ticket types and priorities",
                "data": type_priority_correlation.to_dict()
            })

        return patterns

    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality and completeness"""
        quality = {
            "completeness": {},
            "missing_required_fields": []
        }
        
        for col in self.required_columns:
            if col not in df.columns:
                quality["missing_required_fields"].append(col)
            else:
                completeness = (df[col].notna().sum() / len(df)) * 100
                quality["completeness"][col] = round(completeness, 2)

        return quality
