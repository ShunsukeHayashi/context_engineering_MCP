"""
Context Engineering MCP Package

A comprehensive context management and prompt engineering platform.
"""

from importlib import import_module

from .context_models import (
    ContextElement, ContextWindow, ContextSession,
    PromptTemplate, ContextType, PromptTemplateType,
    ContextQuality, OptimizationStatus,
    ContextAnalysis, OptimizationTask,
    MultimodalContext, RAGContext
)

__version__ = "2.0.0"

_LAZY_IMPORTS = {
    "ContextAnalyzer": (".context_analyzer", "ContextAnalyzer"),
    "MultimodalAnalyzer": (".context_analyzer", "MultimodalAnalyzer"),
    "RAGAnalyzer": (".context_analyzer", "RAGAnalyzer"),
    "TemplateManager": (".template_manager", "TemplateManager"),
    "ContextTemplateIntegrator": (".template_manager", "ContextTemplateIntegrator"),
    "ContextOptimizer": (".context_optimizer", "ContextOptimizer"),
}

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


def __getattr__(name):
    """Lazily import heavy runtime dependencies on first access."""
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute = _LAZY_IMPORTS[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attribute)
    globals()[name] = value
    return value
