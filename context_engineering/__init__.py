"""
Context Engineering MCP Package

A comprehensive context management and prompt engineering platform.
"""

from .context_models import (
    ContextElement, ContextWindow, ContextSession,
    PromptTemplate, ContextType, PromptTemplateType,
    ContextQuality, OptimizationStatus,
    ContextAnalysis, OptimizationTask,
    MultimodalContext, RAGContext
)
from .context_analyzer import ContextAnalyzer, MultimodalAnalyzer, RAGAnalyzer
from .template_manager import TemplateManager, ContextTemplateIntegrator
from .context_optimizer import ContextOptimizer

__version__ = "2.0.0"

__all__ = [
    # Models
    "ContextElement",
    "ContextWindow",
    "ContextSession",
    "PromptTemplate",
    "ContextType",
    "PromptTemplateType",
    "ContextQuality",
    "OptimizationStatus",
    "ContextAnalysis",
    "OptimizationTask",
    "MultimodalContext",
    "RAGContext",
    # Analyzers
    "ContextAnalyzer",
    "MultimodalAnalyzer",
    "RAGAnalyzer",
    # Managers
    "TemplateManager",
    "ContextTemplateIntegrator",
    # Optimizer
    "ContextOptimizer",
]
