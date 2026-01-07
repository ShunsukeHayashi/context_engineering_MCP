"""
Shared test fixtures and configuration for Context Engineering tests.
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, AsyncGenerator
import tempfile
from pathlib import Path

# Set test environment variables
os.environ["GEMINI_API_KEY"] = "test_api_key_12345"
os.environ["NODE_ENV"] = "test"
os.environ["LOG_LEVEL"] = "debug"

@pytest.fixture
def mock_gemini_api():
    """Mock Gemini API for testing."""
    mock = MagicMock()
    mock.generate_content = AsyncMock()
    mock.generate_content.return_value.text = "Mock generated content"
    return mock

@pytest.fixture
def sample_context_element():
    """Sample context element for testing."""
    return {
        "content": "You are a helpful AI assistant.",
        "type": "system",
        "priority": 10,
        "metadata": {"source": "test"}
    }

@pytest.fixture
def sample_context_window():
    """Sample context window for testing."""
    return {
        "name": "Test Context Window",
        "max_tokens": 4096,
        "description": "A test context window"
    }

@pytest.fixture
def sample_template():
    """Sample prompt template for testing."""
    return {
        "name": "Test Template",
        "description": "A test template",
        "template": "You are a {role} with {experience} experience. {task}",
        "type": "completion",
        "category": "test",
        "tags": ["test", "example"]
    }

@pytest.fixture
def temp_storage_dir():
    """Temporary directory for test file storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
async def mock_context_analyzer():
    """Mock ContextAnalyzer for testing."""
    from context_engineering.context_analyzer import ContextAnalyzer
    
    analyzer = MagicMock(spec=ContextAnalyzer)
    analyzer.analyze_context_window = AsyncMock()
    analyzer.analyze_context_window.return_value = MagicMock(
        quality_score=85.0,
        metrics={"total_tokens": 100, "efficiency": 0.8},
        insights=["Good structure", "Clear instructions"],
        recommendations=["Consider reducing redundancy"]
    )
    return analyzer

@pytest.fixture
async def mock_template_manager():
    """Mock TemplateManager for testing."""
    from context_engineering.template_manager import TemplateManager
    
    manager = MagicMock()
    manager.create_template = MagicMock()
    manager.get_template = MagicMock()
    manager.list_templates = MagicMock()
    manager.render_template = AsyncMock()
    manager.generate_template = AsyncMock()
    return manager

@pytest.fixture
async def mock_context_optimizer():
    """Mock ContextOptimizer for testing."""
    from context_engineering.context_optimizer import ContextOptimizer
    
    optimizer = MagicMock()
    optimizer.optimize_context = AsyncMock()
    optimizer.auto_optimize = AsyncMock()
    optimizer.optimize_context.return_value = {
        "optimized_elements": [],
        "metrics": {"token_reduction": 0.3, "quality_improvement": 0.15},
        "explanation": "Optimized for clarity and token efficiency"
    }
    return optimizer

@pytest.fixture
def api_client():
    """Test client for FastAPI application."""
    from fastapi.testclient import TestClient
    from context_engineering.context_api import app
    
    return TestClient(app)

@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing real-time features."""
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_json = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws

class MockGeminiModel:
    """Mock Gemini model for consistent testing."""
    
    def __init__(self, response_text="Mock response"):
        self.response_text = response_text
    
    async def generate_content_async(self, prompt, **kwargs):
        """Mock async content generation."""
        mock_response = MagicMock()
        mock_response.text = self.response_text
        return mock_response
    
    def generate_content(self, prompt, **kwargs):
        """Mock sync content generation."""
        mock_response = MagicMock()
        mock_response.text = self.response_text
        return mock_response

@pytest.fixture
def mock_gemini_model():
    """Fixture providing mock Gemini model."""
    return MockGeminiModel()

# Performance testing fixtures
@pytest.fixture
def performance_benchmark():
    """Benchmark timing for performance tests."""
    import time
    
    class Benchmark:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def end(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
    
    return Benchmark()

# Error simulation fixtures
@pytest.fixture
def network_error():
    """Simulate network errors for testing error handling."""
    import httpx
    return httpx.RequestError("Network connection failed")

@pytest.fixture
def api_rate_limit_error():
    """Simulate API rate limit errors."""
    import httpx
    response = MagicMock()
    response.status_code = 429
    response.json.return_value = {"error": "Rate limit exceeded"}
    return httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=response)