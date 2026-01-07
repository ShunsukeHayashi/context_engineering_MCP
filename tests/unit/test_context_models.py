"""
Unit tests for context_models.py

Tests the core data models and their validation logic.
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
    
    def test_estimated_tokens_property(self):
        """Test token estimation property."""
        element = ContextElement(content="This is a test message with some words")
        
        # Rough token estimation: ~1 token per 4 characters
        expected_tokens = len(element.content) // 4
        assert element.estimated_tokens == expected_tokens
    
    def test_context_element_validation(self):
        """Test ContextElement validation."""
        # Test invalid priority
        with pytest.raises(ValueError):
            element = ContextElement(priority=15)  # Should be 1-10
            element.validate()
    
    def test_context_element_serialization(self):
        """Test ContextElement can be serialized."""
        element = ContextElement(
            content="Test",
            type=ContextType.ASSISTANT,
            metadata={"test": True}
        )
        
        # Test that it can be converted to dict (basic serialization)
        element_dict = {
            "id": element.id,
            "content": element.content,
            "type": element.type.value,
            "priority": element.priority
        }
        assert element_dict["content"] == "Test"
        assert element_dict["type"] == "assistant"


class TestContextWindow:
    """Test ContextWindow data model."""
    
    def test_context_window_creation(self):
        """Test basic ContextWindow creation."""
        window = ContextWindow(
            name="Test Window",
            max_tokens=4096
        )
        
        assert window.name == "Test Window"
        assert window.max_tokens == 4096
        assert window.elements == []
        assert window.current_tokens == 0
    
    def test_add_element(self):
        """Test adding elements to context window."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="Test content", priority=8)
        
        window.add_element(element)
        
        assert len(window.elements) == 1
        assert window.elements[0] == element
        assert window.current_tokens > 0
    
    def test_remove_element(self):
        """Test removing elements from context window."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="Test content")
        
        window.add_element(element)
        assert len(window.elements) == 1
        
        window.remove_element(element.id)
        assert len(window.elements) == 0
        assert window.current_tokens == 0
    
    def test_utilization_ratio(self):
        """Test token utilization ratio calculation."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="A" * 400)  # ~100 tokens
        
        window.add_element(element)
        
        expected_ratio = window.current_tokens / window.max_tokens
        assert window.utilization_ratio == expected_ratio
        assert 0 <= window.utilization_ratio <= 1
    
    def test_available_tokens(self):
        """Test available tokens calculation."""
        window = ContextWindow(max_tokens=1000)
        element = ContextElement(content="A" * 400)  # ~100 tokens
        
        window.add_element(element)
        
        assert window.available_tokens == window.max_tokens - window.current_tokens
        assert window.available_tokens >= 0
    
    def test_token_overflow_prevention(self):
        """Test that token overflow is handled."""
        window = ContextWindow(max_tokens=100)
        large_element = ContextElement(content="A" * 1000)  # ~250 tokens
        
        # Should handle gracefully without breaking
        window.add_element(large_element)
        assert len(window.elements) == 1
    
    def test_element_sorting_by_priority(self):
        """Test that elements are sorted by priority."""
        window = ContextWindow(max_tokens=1000)
        
        low_priority = ContextElement(content="Low", priority=3)
        high_priority = ContextElement(content="High", priority=9)
        medium_priority = ContextElement(content="Medium", priority=6)
        
        window.add_element(low_priority)
        window.add_element(high_priority)
        window.add_element(medium_priority)
        
        # Elements should be sorted by priority (high to low)
        priorities = [elem.priority for elem in window.elements]
        assert priorities == sorted(priorities, reverse=True)


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
        """Test automatic variable extraction from template."""
        template = PromptTemplate(
            name="Auto Extract",
            template="You are {role} with {years} years of experience in {field}."
        )
        
        # Variables should be automatically extracted
        expected_vars = {"role", "years", "field"}
        assert set(template.variables) == expected_vars
    
    def test_template_validation(self):
        """Test template validation."""
        # Test empty template
        with pytest.raises(ValueError):
            template = PromptTemplate(name="Empty", template="")
            template.validate()
        
        # Test missing variables
        template = PromptTemplate(
            name="Missing Vars",
            template="Hello {name}",
            variables=["name", "extra_var"]
        )
        # Should warn about extra variables but not fail
    
    def test_template_usage_tracking(self):
        """Test usage count tracking."""
        template = PromptTemplate(name="Usage Test", template="Test")
        
        assert template.usage_count == 0
        
        template.increment_usage()
        assert template.usage_count == 1
        
        template.increment_usage()
        assert template.usage_count == 2


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
        assert session.context_windows == []
        assert isinstance(session.id, str)
    
    def test_add_context_window(self):
        """Test adding context windows to session."""
        session = ContextSession(name="Test")
        window = ContextWindow(name="Test Window")
        
        session.add_context_window(window)
        
        assert len(session.context_windows) == 1
        assert session.context_windows[0] == window
    
    def test_session_statistics(self):
        """Test session statistics calculation."""
        session = ContextSession(name="Stats Test")
        
        window1 = ContextWindow(name="Window 1", max_tokens=1000)
        window2 = ContextWindow(name="Window 2", max_tokens=2000)
        
        # Add some elements
        window1.add_element(ContextElement(content="A" * 100))
        window2.add_element(ContextElement(content="B" * 200))
        
        session.add_context_window(window1)
        session.add_context_window(window2)
        
        stats = session.get_statistics()
        
        assert stats["total_windows"] == 2
        assert stats["total_elements"] == 2
        assert stats["total_tokens"] > 0


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
    
    def test_analysis_validation(self):
        """Test analysis validation."""
        analysis = ContextAnalysis(
            context_id="test",
            quality_score=150.0  # Invalid score > 100
        )
        
        with pytest.raises(ValueError):
            analysis.validate()
    
    def test_analysis_summary(self):
        """Test analysis summary generation."""
        analysis = ContextAnalysis(
            context_id="test",
            quality_score=85.5,
            metrics={"tokens": 100, "efficiency": 0.8},
            insights=["Good structure", "Clear content"],
            issues=["Minor redundancy"],
            recommendations=["Consider shortening"]
        )
        
        summary = analysis.get_summary()
        
        assert "Quality Score: 85.5" in summary
        assert "Good structure" in summary
        assert "Minor redundancy" in summary


class TestOptimizationTask:
    """Test OptimizationTask data model."""
    
    def test_optimization_task_creation(self):
        """Test OptimizationTask creation."""
        task = OptimizationTask(
            context_id="test-context",
            goals=["reduce_tokens", "improve_clarity"]
        )
        
        assert task.context_id == "test-context"
        assert "reduce_tokens" in task.goals
        assert "improve_clarity" in task.goals
        assert task.status == OptimizationStatus.PENDING
    
    def test_task_progress_tracking(self):
        """Test task progress tracking."""
        task = OptimizationTask(context_id="test")
        
        assert task.status == OptimizationStatus.PENDING
        assert task.progress == 0.0
        
        task.update_progress(50.0)
        assert task.progress == 50.0
        
        task.mark_completed({"improvement": 0.3})
        assert task.status == OptimizationStatus.COMPLETED
        assert task.progress == 100.0
        assert task.result is not None
    
    def test_task_failure_handling(self):
        """Test task failure handling."""
        task = OptimizationTask(context_id="test")
        
        task.mark_failed("Test error message")
        
        assert task.status == OptimizationStatus.FAILED
        assert "Test error message" in task.error_message


# Performance and edge case tests
class TestModelPerformance:
    """Test model performance and edge cases."""
    
    def test_large_context_window(self):
        """Test handling of large context windows."""
        window = ContextWindow(max_tokens=100000)  # Large window
        
        # Add many elements
        for i in range(1000):
            element = ContextElement(content=f"Element {i}")
            window.add_element(element)
        
        assert len(window.elements) == 1000
        assert window.current_tokens > 0
        # Should not crash or become unresponsive
    
    def test_unicode_content_handling(self):
        """Test handling of Unicode content."""
        element = ContextElement(
            content="🔥 Unicode test: 日本語 العربية Ελληνικά 🚀"
        )
        
        assert element.content == "🔥 Unicode test: 日本語 العربية Ελληνικά 🚀"
        assert element.estimated_tokens > 0
    
    def test_empty_and_none_values(self):
        """Test handling of empty and None values."""
        # Empty content
        element = ContextElement(content="")
        assert element.content == ""
        assert element.estimated_tokens == 0
        
        # None metadata handling
        element = ContextElement(metadata=None)
        assert element.metadata == {}
    
    @pytest.mark.performance
    def test_token_calculation_performance(self, performance_benchmark):
        """Test token calculation performance."""
        content = "This is a test content. " * 1000  # Large content
        
        performance_benchmark.start()
        element = ContextElement(content=content)
        tokens = element.estimated_tokens
        duration = performance_benchmark.end()
        
        assert tokens > 0
        assert duration < 0.1  # Should complete in less than 100ms