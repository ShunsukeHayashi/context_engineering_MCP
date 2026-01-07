"""
Unit tests for context_models.py

Tests the core data models and their validation logic.
Updated to match v2.0 API.
"""

import pytest
from datetime import datetime
from typing import List
import uuid

from context_engineering.context_models import (
    ContextElement, ContextWindow, ContextSession, PromptTemplate,
    ContextType, PromptTemplateType, ContextQuality, OptimizationStatus,
    ContextAnalysis, OptimizationTask, MultimodalContext, RAGContext
)


class TestContextElement:
    """Test ContextElement data model."""

    def test_context_element_creation(self):
        """Test basic ContextElement creation."""
        element = ContextElement(
            content="Test content",
            type=ContextType.SYSTEM,
            priority=8
        )

        assert element.content == "Test content"
        assert element.type == ContextType.SYSTEM
        assert element.priority == 8
        assert isinstance(element.id, str)
        assert isinstance(element.created_at, datetime)

    def test_context_element_defaults(self):
        """Test ContextElement default values."""
        element = ContextElement()

        assert element.content == ""
        assert element.type == ContextType.USER
        assert element.priority == 5
        assert element.metadata == {}
        assert element.tags == []

    def test_token_count_property(self):
        """Test token count property."""
        element = ContextElement(content="This is a test message with some words")

        # Token count is based on word count * 1.3
        word_count = len(element.content.split())
        expected_tokens = word_count * 1.3
        assert element.token_count == expected_tokens

    def test_context_element_priority_range(self):
        """Test ContextElement priority values."""
        # Test valid priorities
        element_low = ContextElement(priority=1)
        element_high = ContextElement(priority=10)

        assert element_low.priority == 1
        assert element_high.priority == 10

    def test_context_element_serialization(self):
        """Test ContextElement can be serialized via to_dict()."""
        element = ContextElement(
            content="Test",
            type=ContextType.ASSISTANT,
            metadata={"test": True}
        )

        element_dict = element.to_dict()

        assert element_dict["content"] == "Test"
        assert element_dict["type"] == "assistant"
        assert element_dict["metadata"] == {"test": True}


class TestContextWindow:
    """Test ContextWindow data model."""

    def test_context_window_creation(self):
        """Test basic ContextWindow creation."""
        window = ContextWindow(max_tokens=4096)

        assert window.max_tokens == 4096
        assert window.elements == []
        assert window.current_tokens == 0
        assert window.reserved_tokens == 512  # default

    def test_add_element(self):
        """Test adding elements to context window."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="Test content", priority=8)

        result = window.add_element(element)

        assert result == True
        assert len(window.elements) == 1
        assert window.elements[0] == element
        assert window.current_tokens > 0

    def test_remove_element(self):
        """Test removing elements from context window."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="Test content")

        window.add_element(element)
        assert len(window.elements) == 1

        result = window.remove_element(element.id)
        assert result == True
        assert len(window.elements) == 0
        assert window.current_tokens == 0

    def test_utilization_ratio(self):
        """Test token utilization ratio calculation."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="word " * 100)  # 100 words

        window.add_element(element)

        expected_ratio = window.current_tokens / window.max_tokens
        assert window.utilization_ratio == expected_ratio
        assert 0 <= window.utilization_ratio <= 1

    def test_available_tokens(self):
        """Test available tokens calculation (includes reserved_tokens)."""
        window = ContextWindow(max_tokens=1000, reserved_tokens=100)
        element = ContextElement(content="word " * 10)  # Some words

        window.add_element(element)

        # available_tokens = max_tokens - current_tokens - reserved_tokens
        expected = window.max_tokens - window.current_tokens - window.reserved_tokens
        assert window.available_tokens == expected

    def test_token_overflow_prevention(self):
        """Test that token overflow is prevented by add_element."""
        window = ContextWindow(max_tokens=100, reserved_tokens=50)
        # This creates an element with ~130 tokens (100 words * 1.3)
        large_element = ContextElement(content="word " * 100)

        # Should return False and not add the element
        result = window.add_element(large_element)
        assert result == False
        assert len(window.elements) == 0

    def test_optimize_for_tokens(self):
        """Test optimize_for_tokens removes low priority elements."""
        window = ContextWindow(max_tokens=100, reserved_tokens=10)

        low_priority = ContextElement(content="Low priority content", priority=2)
        high_priority = ContextElement(content="High priority content", priority=9)

        # Force add elements by directly appending
        window.elements.append(low_priority)
        window.elements.append(high_priority)

        result = window.optimize_for_tokens()

        # Should have optimization info
        assert "removed_elements" in result
        assert "tokens_saved" in result


class TestPromptTemplate:
    """Test PromptTemplate data model."""

    def test_prompt_template_creation(self):
        """Test basic PromptTemplate creation."""
        template = PromptTemplate(
            name="Test Template",
            description="A test template",
            template="Hello {name}, you are a {role}",
            variables=["name", "role"]
        )

        assert template.name == "Test Template"
        assert template.description == "A test template"
        assert "name" in template.variables
        assert "role" in template.variables
        assert template.type == PromptTemplateType.COMPLETION

    def test_template_variable_extraction(self):
        """Test variable extraction from template using extract_variables()."""
        template = PromptTemplate(
            name="Auto Extract",
            template="You are {role} with {years} years of experience in {field}."
        )

        # Use the extract_variables method
        extracted = template.extract_variables()
        expected_vars = {"role", "years", "field"}
        assert set(extracted) == expected_vars

    def test_template_render(self):
        """Test template rendering with variables."""
        template = PromptTemplate(
            name="Render Test",
            template="Hello {name}, you are a {role}",
            variables=["name", "role"]
        )

        rendered = template.render({"name": "Alice", "role": "developer"})
        assert rendered == "Hello Alice, you are a developer"

    def test_template_usage_count(self):
        """Test usage count default value."""
        template = PromptTemplate(name="Usage Test", template="Test")

        assert template.usage_count == 0

        # Manually increment (no method exists)
        template.usage_count += 1
        assert template.usage_count == 1


class TestContextSession:
    """Test ContextSession data model."""

    def test_context_session_creation(self):
        """Test basic ContextSession creation."""
        session = ContextSession(
            name="Test Session",
            description="A test session"
        )

        assert session.name == "Test Session"
        assert session.description == "A test session"
        assert session.windows == []
        assert isinstance(session.id, str)

    def test_create_window(self):
        """Test creating context windows in session."""
        session = ContextSession(name="Test")

        window = session.create_window(max_tokens=2000)

        assert len(session.windows) == 1
        assert window.max_tokens == 2000
        assert session.active_window_id == window.id

    def test_get_active_window(self):
        """Test getting active window."""
        session = ContextSession(name="Test")

        # No active window initially
        assert session.get_active_window() is None

        # Create a window
        window = session.create_window()

        # Now should return the window
        active = session.get_active_window()
        assert active is not None
        assert active.id == window.id


class TestContextAnalysis:
    """Test ContextAnalysis data model."""

    def test_context_analysis_creation(self):
        """Test ContextAnalysis creation."""
        analysis = ContextAnalysis(
            context_id="test-context-123",
            analysis_type="comprehensive"
        )

        assert analysis.context_id == "test-context-123"
        assert analysis.analysis_type == "comprehensive"
        assert analysis.quality_score == 0.0
        assert analysis.metrics == {}
        assert analysis.insights == []

    def test_analysis_with_data(self):
        """Test analysis with full data."""
        analysis = ContextAnalysis(
            context_id="test",
            analysis_type="quality",
            quality_score=85.5,
            metrics={"tokens": 100, "efficiency": 0.8},
            insights=["Good structure", "Clear content"],
            issues=["Minor redundancy"],
            recommendations=["Consider shortening"]
        )

        assert analysis.quality_score == 85.5
        assert len(analysis.insights) == 2
        assert len(analysis.issues) == 1
        assert len(analysis.recommendations) == 1

    def test_analysis_to_dict(self):
        """Test analysis serialization."""
        analysis = ContextAnalysis(
            context_id="test",
            analysis_type="basic",
            quality_score=75.0
        )

        result = analysis.to_dict()

        assert result["context_id"] == "test"
        assert result["analysis_type"] == "basic"
        assert result["quality_score"] == 75.0


class TestOptimizationTask:
    """Test OptimizationTask data model."""

    def test_optimization_task_creation(self):
        """Test OptimizationTask creation."""
        task = OptimizationTask(
            context_id="test-context",
            optimization_type="token_reduction"
        )

        assert task.context_id == "test-context"
        assert task.optimization_type == "token_reduction"
        assert task.status == OptimizationStatus.PENDING
        assert task.progress == 0.0

    def test_task_status_values(self):
        """Test task status enum values."""
        task = OptimizationTask(context_id="test")

        assert task.status == OptimizationStatus.PENDING

        # Change status manually
        task.status = OptimizationStatus.IN_PROGRESS
        assert task.status == OptimizationStatus.IN_PROGRESS

        task.status = OptimizationStatus.COMPLETED
        assert task.status == OptimizationStatus.COMPLETED

    def test_task_failure_status(self):
        """Test task failure status."""
        task = OptimizationTask(context_id="test")

        task.status = OptimizationStatus.FAILED
        task.error_message = "Test error message"

        assert task.status == OptimizationStatus.FAILED
        assert task.error_message == "Test error message"


class TestMultimodalContext:
    """Test MultimodalContext data model."""

    def test_multimodal_context_creation(self):
        """Test MultimodalContext creation."""
        context = MultimodalContext(
            text_content="Test text",
            image_urls=["http://example.com/image.png"]
        )

        assert context.text_content == "Test text"
        assert len(context.image_urls) == 1
        assert context.processing_status == "pending"

    def test_total_token_estimate(self):
        """Test token estimation for multimodal content."""
        context = MultimodalContext(
            text_content="This is some text content",
            image_urls=["img1.png", "img2.png"]
        )

        # Should include text tokens + image tokens (1000 per image)
        assert context.total_token_estimate > 2000


class TestRAGContext:
    """Test RAGContext data model."""

    def test_rag_context_creation(self):
        """Test RAGContext creation."""
        context = RAGContext(query="What is machine learning?")

        assert context.query == "What is machine learning?"
        assert context.retrieved_documents == []
        assert context.similarity_scores == []

    def test_add_retrieved_document(self):
        """Test adding retrieved documents."""
        context = RAGContext(query="test")

        doc = {"content": "Test document content", "source": "test.pdf"}
        context.add_retrieved_document(doc, 0.95)

        assert len(context.retrieved_documents) == 1
        assert len(context.similarity_scores) == 1
        assert context.similarity_scores[0] == 0.95

    def test_synthesize_context(self):
        """Test context synthesis from retrieved documents."""
        context = RAGContext(query="test")

        context.add_retrieved_document({"content": "Document A content"}, 0.9)
        context.add_retrieved_document({"content": "Document B content"}, 0.8)

        result = context.synthesize_context(max_tokens=1000)

        assert len(result) > 0
        assert context.context_synthesis == result


# Performance and edge case tests
class TestModelPerformance:
    """Test model performance and edge cases."""

    def test_large_context_window(self):
        """Test handling of large context windows."""
        window = ContextWindow(max_tokens=100000)  # Large window

        # Add many elements
        for i in range(100):
            element = ContextElement(content=f"Element {i}")
            window.add_element(element)

        assert len(window.elements) == 100
        assert window.current_tokens > 0

    def test_unicode_content_handling(self):
        """Test handling of Unicode content."""
        element = ContextElement(
            content="Unicode test: 日本語 العربية Ελληνικά"
        )

        assert "日本語" in element.content
        assert element.token_count > 0

    def test_empty_content(self):
        """Test handling of empty content."""
        element = ContextElement(content="")
        assert element.content == ""
        assert element.token_count == 0

    def test_token_calculation_speed(self):
        """Test token calculation is fast."""
        import time

        content = "This is a test content. " * 1000  # Large content

        start = time.time()
        element = ContextElement(content=content)
        tokens = element.token_count
        duration = time.time() - start

        assert tokens > 0
        assert duration < 0.1  # Should complete in less than 100ms
