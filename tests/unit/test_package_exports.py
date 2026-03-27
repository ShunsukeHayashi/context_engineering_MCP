"""
Unit tests for package-level exports and lazy imports.
"""

from __future__ import annotations

import context_engineering


def test_package_version_and_lazy_exports():
    assert context_engineering.__version__ == "2.0.0"
    assert "ContextOptimizer" in context_engineering.__all__

    exported = context_engineering.ContextOptimizer

    assert exported.__name__ == "ContextOptimizer"


def test_package_getattr_raises_for_unknown_symbol():
    try:
        getattr(context_engineering, "DoesNotExist")
    except AttributeError as exc:
        assert "DoesNotExist" in str(exc)
    else:
        raise AssertionError("AttributeError was not raised")
