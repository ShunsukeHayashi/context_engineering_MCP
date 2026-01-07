"""
Context Engineering MCP Platform - Test Suite

This package contains comprehensive tests for the Context Engineering platform.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for API endpoints
- e2e/: End-to-end tests for complete workflows
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure asyncio for tests
pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()