# """
# Base test configuration and utilities for ProcessLens
# """
# import pytest
# import asyncio
# from typing import Any, Dict, Generator
# from motor.motor_asyncio import AsyncIOMotorClient
# from unittest.mock import AsyncMock, patch
# import pandas as pd
# import os
# from dotenv import load_dotenv

# # Load test environment variables
# load_dotenv(".env.test")

# class BaseProcessLensTest:
#     """Base test class with common utilities"""
    
#     @pytest.fixture(autouse=True)
#     def setup_test_db(self) -> Generator:
#         """Setup test database connection"""
#         self.db_client = AsyncIOMotorClient(os.getenv("MONGODB_TEST_URL"))
#         self.test_db = self.db_client.processlens_test
#         yield
#         self.db_client.close()

#     @pytest.fixture
#     def mock_watson_llm(self) -> AsyncMock:
#         """Mock WatsonxLLM for testing"""
#         with patch("langchain_ibm.WatsonxLLM") as mock:
#             mock.return_value.agenerate = AsyncMock()
#             yield mock.return_value

#     @pytest.fixture
#     def mock_gemini_client(self) -> AsyncMock:
#         """Mock Gemini client for testing"""
#         with patch("google.genai.Client") as mock:
#             mock.return_value.models.generate_content = AsyncMock()
#             yield mock.return_value

#     @pytest.fixture
#     def sample_dataset(self) -> pd.DataFrame:
#         """Create sample dataset for testing"""
#         return pd.DataFrame({
#             "id": range(100),
#             "type": ["A", "B"] * 50,
#             "created_at": pd.date_range(start="2024-01-01", periods=100),
#             "status": ["open", "closed"] * 50
#         })

#     @staticmethod
#     def assert_json_structure(data: Dict[str, Any], required_keys: set) -> None:
#         """Assert that JSON response has required structure"""
#         assert isinstance(data, dict), "Response must be a dictionary"
#         assert all(key in data for key in required_keys), f"Missing required keys: {required_keys - set(data.keys())}"

#     @staticmethod
#     async def mock_analysis_response() -> Dict[str, Any]:
#         """Generate mock analysis response"""
#         return {
#             "status": "success",
#             "insights": ["Sample insight 1", "Sample insight 2"],
#             "metrics": {
#                 "processing_time": 120,
#                 "success_rate": 0.95
#             }
#         }