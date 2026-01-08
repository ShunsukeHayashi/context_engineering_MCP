"""
Integration tests for Context Engineering API endpoints.

Tests the FastAPI application with real HTTP requests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json

# Mock response data for Gemini AI
MOCK_AI_RESPONSE = json.dumps({
    "quality_score": 75,
    "insights": ["Good structure", "Clear content"],
    "recommendations": ["Consider adding more context"],
    "issues": [],
    "strengths": ["Well organized"],
    "metrics": {
        "coherence": 0.85,
        "completeness": 0.80,
        "relevance": 0.90
    },
    "score": 75,
    "name": "Generated Template",
    "template": "You are a {role} assistant.",
    "variables": ["role"],
    "description": "A generated template",
    "type": "completion",
    "category": "general",
    "tags": ["ai-generated"],
    "recommended_goals": ["improve_clarity", "reduce_tokens"],
    "optimized_content": "Optimized content here",
    "tokens_saved": 50,
    "clarity_score": 85,
    "optimization_type": "auto",
    "task_id": "test-task-123"
})


# We'll need to mock the Gemini API for testing
@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    import os
    import asyncio

    # Set dummy API key for testing
    os.environ['GEMINI_API_KEY'] = 'test-api-key-for-testing'

    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as mock_model:

        # Mock the Gemini model - return sync mock with comprehensive response
        mock_response = MagicMock()
        mock_response.text = MOCK_AI_RESPONSE

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_instance.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model.return_value = mock_instance

        from context_engineering.context_api import app, initialize_components

        # Initialize components that are normally initialized during lifespan
        try:
            asyncio.get_event_loop().run_until_complete(initialize_components())
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(initialize_components())

        yield TestClient(app)


class TestSessionManagement:
    """Test session management endpoints."""
    
    @pytest.mark.api
    def test_create_session(self, client):
        """Test creating a new context session."""
        response = client.post(
            "/api/sessions",
            params={"name": "Test Session", "description": "Test description"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Session"
        assert data["description"] == "Test description"
        assert "session_id" in data
        assert "created_at" in data
    
    @pytest.mark.api
    def test_list_sessions(self, client):
        """Test listing all sessions."""
        # First create a session
        client.post("/api/sessions", params={"name": "Test Session"})
        
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1
    
    @pytest.mark.api
    def test_get_session_details(self, client):
        """Test getting session details."""
        # Create a session first
        create_response = client.post("/api/sessions", params={"name": "Detail Test"})
        session_id = create_response.json()["session_id"]

        response = client.get(f"/api/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id  # API returns 'id' not 'session_id'
        assert data["name"] == "Detail Test"
    
    @pytest.mark.api
    def test_get_nonexistent_session(self, client):
        """Test getting details of non-existent session."""
        response = client.get("/api/sessions/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestContextWindows:
    """Test context window management endpoints."""
    
    @pytest.fixture
    def session_id(self, client):
        """Create a session for testing context windows."""
        response = client.post("/api/sessions", params={"name": "Window Test Session"})
        return response.json()["session_id"]
    
    @pytest.mark.api
    def test_create_context_window(self, client, session_id):
        """Test creating a context window."""
        window_data = {
            "max_tokens": 4096,
            "reserved_tokens": 512
        }

        response = client.post(
            f"/api/sessions/{session_id}/windows",
            json=window_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["max_tokens"] == 4096
        assert "window_id" in data
    
    @pytest.mark.api
    def test_add_context_element(self, client, session_id):
        """Test adding an element to a context window."""
        # First create a window
        window_response = client.post(
            f"/api/sessions/{session_id}/windows",
            json={"max_tokens": 2048}
        )
        window_id = window_response.json()["window_id"]

        # Add an element
        element_data = {
            "content": "You are a helpful AI assistant.",
            "type": "system",
            "priority": 10,
            "metadata": {"source": "test"}
        }

        response = client.post(
            f"/api/contexts/{window_id}/elements",
            json=element_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "element_id" in data
        assert "current_tokens" in data
        assert "utilization_ratio" in data
    
    @pytest.mark.api
    def test_get_context_window(self, client, session_id):
        """Test retrieving a context window with its elements."""
        # Create window and add element
        window_response = client.post(
            f"/api/sessions/{session_id}/windows",
            json={"max_tokens": 1024}
        )
        window_id = window_response.json()["window_id"]

        client.post(
            f"/api/contexts/{window_id}/elements",
            json={"content": "Test content", "type": "user"}
        )

        # Retrieve the window
        response = client.get(f"/api/contexts/{window_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == window_id  # API returns 'id' not 'window_id'
        assert len(data["elements"]) == 1
        assert "current_tokens" in data
        assert "utilization_ratio" in data


class TestContextAnalysis:
    """Test context analysis endpoints."""
    
    @pytest.fixture
    def window_with_content(self, client):
        """Create a context window with content for analysis."""
        # Create session
        session_response = client.post("/api/sessions", params={"name": "Analysis Test"})
        session_id = session_response.json()["session_id"]
        
        # Create window
        window_response = client.post(
            f"/api/sessions/{session_id}/windows",
            json={"name": "Analysis Window", "max_tokens": 2048}
        )
        window_id = window_response.json()["window_id"]
        
        # Add some content
        client.post(
            f"/api/contexts/{window_id}/elements",
            json={
                "content": "You are a helpful assistant that provides detailed explanations.",
                "type": "system",
                "priority": 10
            }
        )
        
        client.post(
            f"/api/contexts/{window_id}/elements",
            json={
                "content": "Please explain quantum computing in simple terms.",
                "type": "user",
                "priority": 5
            }
        )
        
        return window_id
    
    @pytest.mark.api
    @pytest.mark.ai
    def test_analyze_context(self, client, window_with_content):
        """Test context analysis endpoint."""
        window_id = window_with_content

        response = client.post(f"/api/contexts/{window_id}/analyze")

        assert response.status_code == 200
        data = response.json()
        assert "context_id" in data  # API returns context_id, not analysis_id
        assert "quality_score" in data
        assert "metrics" in data
        assert "insights" in data
        assert data["quality_score"] >= 0
        assert data["quality_score"] <= 100


class TestTemplateManagement:
    """Test template management endpoints."""
    
    @pytest.mark.api
    @pytest.mark.template
    def test_create_template(self, client):
        """Test creating a prompt template."""
        template_data = {
            "name": "Test Template",
            "description": "A test template",
            "template": "You are a {role} with {experience} years of experience.",
            "type": "completion",
            "category": "test",
            "tags": ["test", "example"]
        }

        response = client.post("/api/templates", json=template_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == template_data["name"]
        assert "template_id" in data
        assert "variables" in data
        # Variables are extracted from template string
        assert "role" in data["variables"]
        assert "experience" in data["variables"]
    
    @pytest.mark.api
    @pytest.mark.template
    def test_list_templates(self, client):
        """Test listing templates."""
        # Create a template first
        client.post("/api/templates", json={
            "name": "List Test Template",
            "description": "Test template for listing",
            "template": "Test {variable}",
            "category": "test"
        })

        response = client.get("/api/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 1

    @pytest.mark.api
    @pytest.mark.template
    def test_render_template(self, client):
        """Test rendering a template with variables."""
        # Create a template
        template_response = client.post("/api/templates", json={
            "name": "Render Test",
            "description": "Template for render testing",
            "template": "Hello {name}, you are a {role}!",
            "category": "test"
        })
        template_id = template_response.json()["template_id"]

        # Render it - include template_id in body as required by TemplateRenderRequest
        render_data = {
            "template_id": template_id,
            "variables": {
                "name": "Alice",
                "role": "developer"
            }
        }

        response = client.post(f"/api/templates/{template_id}/render", json=render_data)

        assert response.status_code == 200
        data = response.json()
        assert "rendered_content" in data
        assert "Hello Alice, you are a developer!" == data["rendered_content"]
    
    @pytest.mark.api
    @pytest.mark.template
    @pytest.mark.ai
    def test_generate_template(self, client):
        """Test AI-powered template generation."""
        response = client.post(
            "/api/templates/generate",
            params={
                "purpose": "Create a customer service chatbot response",
                "examples": "Handle complaints,Provide product information",
                "constraints": "Professional tone,Maximum 100 words"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "template_id" in data
        assert "template" in data
        assert "variables" in data


class TestContextOptimization:
    """Test context optimization endpoints."""
    
    @pytest.fixture
    def optimizable_window(self, client):
        """Create a context window suitable for optimization testing."""
        # Create session and window
        session_response = client.post("/api/sessions", params={"name": "Optimization Test"})
        session_id = session_response.json()["session_id"]
        
        window_response = client.post(
            f"/api/sessions/{session_id}/windows",
            json={"name": "Optimization Window", "max_tokens": 4096}
        )
        window_id = window_response.json()["window_id"]
        
        # Add redundant content for optimization
        client.post(
            f"/api/contexts/{window_id}/elements",
            json={
                "content": "You are a helpful assistant. You are very helpful. You help users with their questions. You provide helpful responses to users.",
                "type": "system",
                "priority": 10
            }
        )
        
        return window_id
    
    @pytest.mark.api
    @pytest.mark.optimization
    @pytest.mark.ai
    def test_optimize_context(self, client, optimizable_window):
        """Test context optimization with specific goals."""
        window_id = optimizable_window
        
        optimization_data = {
            "goals": ["reduce_tokens", "improve_clarity"],
            "constraints": {"min_tokens": 50}
        }
        
        response = client.post(
            f"/api/contexts/{window_id}/optimize",
            json=optimization_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        # API returns "goals" not "optimization_goals"
        assert "goals" in data
        assert "reduce_tokens" in data["goals"]
    
    @pytest.mark.api
    @pytest.mark.optimization
    @pytest.mark.ai
    def test_auto_optimize_context(self, client, optimizable_window):
        """Test automatic context optimization."""
        window_id = optimizable_window
        
        response = client.post(f"/api/contexts/{window_id}/auto-optimize")

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        # API returns "optimization_started" not "status"
        assert "optimization_started" in data
    
    @pytest.mark.api
    def test_get_optimization_task(self, client, optimizable_window):
        """Test retrieving optimization task status."""
        window_id = optimizable_window
        
        # Start an optimization
        opt_response = client.post(f"/api/contexts/{window_id}/auto-optimize")
        task_id = opt_response.json()["task_id"]
        
        # Check task status
        response = client.get(f"/api/optimization/{task_id}")

        assert response.status_code == 200
        data = response.json()
        # API returns "id" not "task_id"
        assert data["id"] == task_id
        assert "status" in data
        assert "progress" in data


class TestSystemEndpoints:
    """Test system and utility endpoints."""
    
    @pytest.mark.api
    def test_get_stats(self, client):
        """Test system statistics endpoint."""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        # API returns nested structure
        assert "sessions" in data
        assert "contexts" in data
        assert "templates" in data
        # Check nested values exist
        assert "total" in data["sessions"]
        assert "total_windows" in data["contexts"]
        # templates uses "total_templates" not "total"
        assert "total_templates" in data["templates"]
    
    @pytest.mark.api
    def test_dashboard_endpoint(self, client):
        """Test dashboard HTML endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Test API error handling and edge cases."""
    
    @pytest.mark.api
    def test_invalid_session_id(self, client):
        """Test handling of invalid session IDs."""
        response = client.get("/api/sessions/invalid-session-id")
        
        assert response.status_code == 404
        assert "error" in response.json() or "detail" in response.json()
    
    @pytest.mark.api
    def test_invalid_window_id(self, client):
        """Test handling of invalid window IDs."""
        response = client.get("/api/contexts/invalid-window-id")
        
        assert response.status_code == 404
    
    @pytest.mark.api
    def test_malformed_request_data(self, client):
        """Test handling of malformed request data."""
        response = client.post("/api/templates", json={"invalid": "data"})
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    def test_empty_content_element(self, client):
        """Test handling of empty content in context elements."""
        # Create session and window
        session_response = client.post("/api/sessions", params={"name": "Empty Test"})
        session_id = session_response.json()["session_id"]
        
        window_response = client.post(
            f"/api/sessions/{session_id}/windows",
            json={"name": "Empty Window", "max_tokens": 1024}
        )
        window_id = window_response.json()["window_id"]
        
        # Try to add empty element
        response = client.post(
            f"/api/contexts/{window_id}/elements",
            json={"content": "", "type": "user"}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]  # Depends on validation rules


# Performance tests
class TestAPIPerformance:
    """Test API performance under various conditions."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_content_handling(self, client, performance_benchmark):
        """Test API performance with large content."""
        # Create session and window
        session_response = client.post("/api/sessions", params={"name": "Performance Test"})
        session_id = session_response.json()["session_id"]
        
        window_response = client.post(
            f"/api/sessions/{session_id}/windows",
            json={"name": "Large Content Window", "max_tokens": 50000}
        )
        window_id = window_response.json()["window_id"]
        
        # Add large content
        large_content = "This is a test sentence. " * 1000  # ~5000 words
        
        performance_benchmark.start()
        response = client.post(
            f"/api/contexts/{window_id}/elements",
            json={"content": large_content, "type": "user"}
        )
        duration = performance_benchmark.end()
        
        assert response.status_code == 200
        assert duration < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.performance
    def test_concurrent_session_creation(self, client):
        """Test handling of multiple concurrent session creations."""
        import threading
        import time
        
        results = []
        
        def create_session(index):
            response = client.post("/api/sessions", params={"name": f"Concurrent {index}"})
            results.append(response.status_code)
        
        # Create 10 concurrent sessions
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10