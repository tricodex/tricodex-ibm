"""
MongoDB data serialization utilities for ProcessLens
"""
from typing import Any, Dict, List, Union
import pandas as pd
from datetime import datetime
import numpy as np
import json

class MongoDBSerializer:
    """Serializer for MongoDB-compatible data structures"""
    
    @classmethod
    def serialize_for_mongodb(cls, data: Any) -> Any:
        """Convert data structure to MongoDB-compatible format"""
        if isinstance(data, dict):
            return {
                cls._serialize_key(k): cls.serialize_for_mongodb(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [cls.serialize_for_mongodb(item) for item in data]
        elif isinstance(data, tuple):
            return [cls.serialize_for_mongodb(item) for item in data]
        elif isinstance(data, (pd.Timestamp, datetime)):
            return data.isoformat()
        elif isinstance(data, (np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.float64, np.float32)):
            return float(data)
        elif pd.isna(data):
            return None
        return data
    
    @staticmethod
    def _serialize_key(key: Any) -> str:
        """Convert any key to a valid MongoDB string key"""
        if isinstance(key, (int, float)):
            return f"n_{key}"  # Prefix numeric keys with 'n_'
        elif isinstance(key, (pd.Timestamp, datetime)):
            return f"t_{key.isoformat()}"  # Prefix timestamp keys with 't_'
        elif isinstance(key, bool):
            return f"b_{str(key).lower()}"  # Prefix boolean keys with 'b_'
        return str(key)
    
    @classmethod
    def deserialize_from_mongodb(cls, data: Any) -> Any:
        """Convert MongoDB data back to original format"""
        if isinstance(data, dict):
            return {
                cls._deserialize_key(k): cls.deserialize_from_mongodb(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [cls.deserialize_from_mongodb(item) for item in data]
        return data
    
    @staticmethod
    def _deserialize_key(key: str) -> Union[str, float, datetime, bool]:
        """Convert serialized key back to original type"""
        if key.startswith('n_'):
            try:
                num = float(key[2:])
                return int(num) if num.is_integer() else num
            except ValueError:
                return key
        elif key.startswith('t_'):
            try:
                return datetime.fromisoformat(key[2:])
            except ValueError:
                return key
        elif key.startswith('b_'):
            return key[2:] == 'true'
        return key

def serialize_analysis_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize analysis results for MongoDB storage"""
    serializer = MongoDBSerializer()
    
    # Handle special cases for analysis results
    def _process_value_counts(data: Dict[str, Any]) -> Dict[str, Any]:
        if 'top_values' in data:
            # Convert value_counts to list of tuples for consistent ordering
            top_values = data['top_values']
            data['top_values'] = {
                serializer._serialize_key(k): v
                for k, v in top_values.items()
            }
        return data
    
    def _process_warnings(warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for warning in warnings:
            if 'missing_rate' in warning:
                warning['missing_rate'] = float(warning['missing_rate'])
        return warnings
    
    # Process the results
    serialized = {}
    for key, value in results.items():
        if isinstance(value, dict):
            if 'field_stats' in value:
                # Handle field statistics
                value['field_stats'] = {
                    k: _process_value_counts(v)
                    for k, v in value['field_stats'].items()
                }
            if 'warnings' in value:
                # Handle warnings
                value['warnings'] = _process_warnings(value['warnings'])
                
        serialized[key] = serializer.serialize_for_mongodb(value)
    
    return serialized

def deserialize_analysis_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize analysis results from MongoDB storage"""
    serializer = MongoDBSerializer()
    return serializer.deserialize_from_mongodb(data)